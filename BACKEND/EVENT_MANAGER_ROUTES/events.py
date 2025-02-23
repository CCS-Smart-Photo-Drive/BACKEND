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



# Upload to Google
from google.cloud import storage
import asyncio
import os

# Set the environment variable to use the service account

async def upload_to_gcs(event_folder, event_name):
    try:
        client = storage.Client()
        bucket_name = "ccs-host.appspot.com"
        bucket = client.bucket(bucket_name)

        tasks = []

        for image_file in os.listdir(event_folder):
            image_path = os.path.join(event_folder, image_file)
            if os.path.isfile(image_path):
                blob_name = f"upload_folder/{event_name}/{image_file}"
                blob = bucket.blob(blob_name)

                # Asynchronous upload
                task = asyncio.to_thread(blob.upload_from_filename, image_path)
                tasks.append(task)

        await asyncio.gather(*tasks)

        print(f"Uploaded all images to GCS under event: {event_name}")

    except Exception as e:
        print(f"Error uploading files: {e}")



# Event_manager Dashboard
@app.route('/add_new_event', methods=['POST'])
async def add_new_event():
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
        if events_collection.find_one({'event_manager_name': event_manager_name}) and events_collection.find_one(
                {'event_name': event_name}):
            return jsonify({'error': 'Event Already exists'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 400

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected for uploading'}), 400

    if not (file and file.filename.endswith('.zip')):
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
    print(tic_start)
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(event_folder)
    except (zipfile.BadZipFile, OSError):
        return jsonify({'error': 'Error extracting the zip file'}), 500

    try:
        for idx, extracted_file in enumerate(os.listdir(event_folder), start=1):
            extracted_file_path = os.path.join(event_folder, extracted_file)
            if not os.path.isfile(extracted_file_path):
                continue
            file_ext = os.path.splitext(extracted_file)[1]
            new_filename = f"{event_name}_{idx}{file_ext}"
            new_file_path = os.path.join(event_folder, new_filename)
            os.rename(extracted_file_path, new_file_path)
    except OSError as e:
        print(e)
        return jsonify({'error': 'Error renaming the files'}), 500
    tic_mid = time()
    print(tic_mid-tic_start)
    print("BEFORE MODEL")
    response = await play.generate_event_embeddings(event_folder, event_name)
    if not response:
        return jsonify({'error': 'Error processing event embeddings'}), 500
    print("BEFORE GCS UPLOAD")
    tic_mid2 = time()
    print(tic_mid2-tic_mid)
    gcs_result = await upload_to_gcs(event_folder, event_name)
    if gcs_result is not True:
        return jsonify({'error': f'Error uploading to GCS: {gcs_result}'}), 500

    tic_end = time()
    print(tic_end-tic_mid2)
    try:
        shutil.rmtree(event_folder)
        os.remove(file_path)
    except OSError as e:
        return jsonify({'error': f'Error deleting local files: {str(e)}'}), 500
    try:
        events_collection.insert_one(event)
    except:
        return jsonify({'error': 'couldnt uplaod to mongo'}), 500

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