import os
import zipfile
import shutil
from flask import request, jsonify, g
import bcrypt
import BACKEND.config
from werkzeug.utils import secure_filename
from FACE_MODEL import play
from BACKEND.init_config import events_collection, app
import asyncio
from time import time

import uuid


# Upload to Google
from google.cloud import storage
import asyncio
import os




# Google Cloud Storage setup



from concurrent.futures import ThreadPoolExecutor


# Google Cloud Storage setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_PATH = os.path.join(BASE_DIR, "..", "config", "serviceAccount.json")

client_gcs = storage.Client.from_service_account_json(SERVICE_ACCOUNT_PATH)
bucket_name = "ccs-host.appspot.com"
bucket = client_gcs.bucket(bucket_name)

executor = ThreadPoolExecutor(max_workers=10)  # Adjust max workers based on available resources

async def upload_to_gcs(event_folder, event_name):
    try:
        loop = asyncio.get_event_loop()
        public_urls = []

        async def upload_and_make_public(image_file):
            """Uploads file to GCS and makes it public"""
            image_path = os.path.join(event_folder, image_file)
            if os.path.isfile(image_path):
                blob_name = f"upload_folder/{event_name}/{image_file}"
                blob = bucket.blob(blob_name)

                # Upload file asynchronously
                await loop.run_in_executor(executor, blob.upload_from_filename, image_path)

                # Make file public
                await loop.run_in_executor(executor, blob.make_public)
                public_urls.append(blob.public_url)

        # Run uploads in parallel
        tasks = [upload_and_make_public(image_file) for image_file in os.listdir(event_folder)]
        await asyncio.gather(*tasks)

        print(f"Uploaded all images to GCS under event: {event_name}")
        return public_urls

    except Exception as e:
        print(f"Error uploading files: {e}")
        return None


async def extract_files(file_path, event_folder):
    """Extracts ZIP files asynchronously"""
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(executor, shutil.unpack_archive, file_path, event_folder)
    except (zipfile.BadZipFile, OSError) as e:
        raise ValueError(f"Error extracting ZIP file: {str(e)}")


@app.route('/add_new_event', methods=['POST'])
async def add_new_event():
    event_name = request.form.get('event_name')

    if not event_name:
        return jsonify({'error': 'Event name is required'}), 400

    # Validate file
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.zip'):
        return jsonify({'error': 'Allowed file type is .zip'}), 400

    # Secure filename & prepare paths
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    try:
        file.save(file_path)
    except Exception as e:
        return jsonify({'error': f'File save error: {str(e)}'}), 500

    event_folder = os.path.join(app.config['UPLOAD_FOLDER'], event_name)
    os.makedirs(event_folder, exist_ok=True)

    tic_start = time()

    # Extract files asynchronously
    try:
        await extract_files(file_path, event_folder)
    except ValueError as e:
        return jsonify({'error': str(e)}), 500

    tic_mid = time()
    print(f"Time to extract files: {tic_mid - tic_start:.2f}s")

    # Process embeddings in parallel
    print("Processing embeddings...")
    response = await play.generate_event_embeddings(event_folder, event_name)
    if not response:
        return jsonify({'error': 'Error processing event embeddings'}), 500

    tic_mid2 = time()
    print(f"Time for embedding generation: {tic_mid2 - tic_mid:.2f}s")

    # Upload to GCS in parallel
    print("Uploading to GCS...")
    gcs_urls = await upload_to_gcs(event_folder, event_name)
    if gcs_urls is None:
        return jsonify({'error': 'Error uploading to GCS'}), 500

    tic_end = time()
    print(f"Time for GCS upload: {tic_end - tic_mid2:.2f}s")

    # Clean up local files
    try:
        shutil.rmtree(event_folder)
        os.remove(file_path)
    except OSError as e:
        return jsonify({'error': f'Error deleting local files: {str(e)}'}), 500

    return jsonify({'message': 'Event successfully added', 'image_urls': gcs_urls}), 201



@app.route('/my_events', methods=['POST'])
async def my_events():
    event_manager = g.user['user_name']
    if event_manager == '':
        return jsonify({'error': 'Return Event_Manager Name'}), 400
    events = list(events_collection.find({'event_manager_name': event_manager}))
    for event in events:
        event['_id'] = str(event['_id'])
    return jsonify({'events': events}), 200

@app.route('/remove_event', methods = ['DELETE'])
async def remove_event():
    event_manager = g.user['user_name']
    event_name = request.form['event_name']
    if event_name == '':
        return jsonify({'error': 'Return Event Name'}), 400
    event = events_collection.find_one({'event_manager_name': event_manager, 'event_name': event_name})
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    events_collection.delete_one({'event_manager_name': event_manager, 'event_name': event_name})
    return jsonify({'message': 'Event deleted successfully'}), 200