import os
import zipfile
import shutil
from flask import request, jsonify, g
import bcrypt
import BACKEND.config
from werkzeug.utils import secure_filename
import cloudinary
import cloudinary.uploader
from FACE_MODEL import play
from BACKEND.init_config import events_collection, app
import asyncio
from time import time



# Upload to Google
from google.cloud import storage
import asyncio
import os


# Initialize Google Cloud Storage Client with Service Account
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Directory of this script
SERVICE_ACCOUNT_PATH = os.path.join(BASE_DIR, "..", "config", "serviceAccount.json")

# Initialize the client
client = storage.Client.from_service_account_json(SERVICE_ACCOUNT_PATH)
bucket_name = "ccs-host.appspot.com"
bucket = client.bucket(bucket_name)

async def extract_zip_async(zip_path, extract_to):
    """Extract ZIP file asynchronously using asyncio.to_thread"""
    return await asyncio.to_thread(zipfile.ZipFile(zip_path, 'r').extractall, extract_to)

async def upload_to_gcs(event_folder, event_name):
    """Uploads extracted files to GCS asynchronously"""
    try:
        urls = []
        tasks = []
        
        # List files and upload them concurrently
        for image_file in os.listdir(event_folder):
            image_path = os.path.join(event_folder, image_file)
            if os.path.isfile(image_path):
                blob_name = f"upload_folder/{event_name}/{image_file}"
                blob = bucket.blob(blob_name)

                # Upload asynchronously
                task = asyncio.to_thread(blob.upload_from_filename, image_path)
                tasks.append(task)
                urls.append(f"https://storage.googleapis.com/{bucket_name}/{blob_name}")

        await asyncio.gather(*tasks)  # Upload all files concurrently

        # Make all uploaded files public
        for image_url in urls:
            blob_name = image_url.replace(f"https://storage.googleapis.com/{bucket_name}/", "")
            blob = bucket.blob(blob_name)
            blob.make_public()

        return urls, None  # Return list of public URLs
    except Exception as e:
        return None, str(e)

@app.route('/add_new_event', methods=['POST'])
async def add_new_event():
    """Handles event creation and file uploads"""
    event_manager_name = g.user['user_name']
    event_name = request.form['event_name']
    description = request.form['description']
    organized_by = request.form['organized_by']
    date = request.form['date']

    if not all([event_name, description, organized_by, date]):
        return jsonify({'error': 'All fields are required'}), 400

    event = {
        'event_manager_name': event_manager_name,
        'event_name': event_name,
        'description': description,
        'organized_by': organized_by,
        'date': date
    }

    try:
        if events_collection.find_one({'event_manager_name': event_manager_name}) and events_collection.find_one({'event_name': event_name}):
            return jsonify({'error': 'Event Already exists'}), 400
        events_collection.insert_one(event)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected for uploading'}), 400

    if not file.filename.endswith('.zip'):
        return jsonify({'error': 'Allowed file type is .zip'}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    try:
        file.save(file_path)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    event_folder = os.path.join(app.config['UPLOAD_FOLDER'], event_name)
    os.makedirs(event_folder, exist_ok=True)

    tic_start = time()
    try:
        await extract_zip_async(file_path, event_folder)  # Extract asynchronously
    except zipfile.BadZipFile:
        return jsonify({'error': 'Error extracting the zip file'}), 500

    try:
        # Rename extracted files for uniqueness
        for idx, extracted_file in enumerate(os.listdir(event_folder), start=1):
            extracted_file_path = os.path.join(event_folder, extracted_file)
            if not os.path.isfile(extracted_file_path):
                continue
            file_ext = os.path.splitext(extracted_file)[1]
            new_filename = f"{event_name}_{idx}{file_ext}"
            os.rename(extracted_file_path, os.path.join(event_folder, new_filename))
    except OSError as e:
        return jsonify({'error': 'Error renaming the files'}), 500

    tic_mid = time()
    print(f"Time taken for extraction and renaming: {tic_mid - tic_start:.2f}s")

    # Process event embeddings
    response = await play.generate_event_embeddings(event_folder, event_name)
    if not response:
        return jsonify({'error': 'Error processing event embeddings'}), 500

    tic_mid2 = time()
    print(f"Time taken before cloud upload: {tic_mid2 - tic_mid:.2f}s")

    # Upload extracted files to Google Cloud Storage
    cloudinary_result, err = await upload_to_gcs(event_folder, event_name)
    if err:
        return jsonify({'error': f'Error while uploading images to GCS: {err}'}), 500

    tic_end = time()
    print(f"Time taken for GCS upload: {tic_end - tic_mid2:.2f}s")

    # Cleanup local files
    try:
        shutil.rmtree(event_folder)
        os.remove(file_path)
    except OSError as e:
        return jsonify({'error': f'Error deleting local files: {str(e)}'}), 500

    return jsonify({'message': 'Event successfully added and files uploaded, processed, and cleaned up'}), 201

@app.route('/my_events', methods=['POST'])
async def my_events():
    event_manager = g.user['user_name']
    if event_manager == '':
        return jsonify({'error': 'Return Event_Manager Name'}), 400
    events = list(events_collection.find({'event_manager_name': event_manager}))
    for event in events:
        event['_id'] = str(event['_id'])
    return jsonify({'events': events}), 200