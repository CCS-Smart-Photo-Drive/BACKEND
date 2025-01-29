import os
import zipfile
import shutil
from flask import Flask, request, jsonify
import bcrypt
import BACKEND.config
from werkzeug.utils import secure_filename
import cloudinary
import cloudinary.uploader
from FACE_MODEL import play
from BACKEND.init_config import events_collection, app, event_manager_collection
import asyncio

# Upload to Cloudinary
async def upload_to_cloudinary(event_folder, event_name):
    try:
        tasks = []
        for image_file in os.listdir(event_folder):
            image_path = os.path.join(event_folder, image_file)
            if os.path.isfile(image_path):
                # Upload in a separate thread to avoid blocking
                task = asyncio.to_thread(cloudinary.uploader.upload, image_path, folder=event_name, public_id = image_file)
                tasks.append(task)

        await asyncio.gather(*tasks)  # Run uploads concurrently
        return True
    except Exception as e:
        return str(e)

# Event_manager Dashboard
@app.route('/add_new_event', methods=['POST'])
async def add_new_event():
    event_manager_name = request.form['event_manager_name']
    event_name = request.form['event_name']
    description = request.form['description']
    organized_by = request.form['organized_by']
    date = request.form['date']
    print("yes1")

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
        events_collection.insert_one(event)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected for uploading'}), 400

    if file and file.filename.endswith('.zip'):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        event_folder = os.path.join(app.config['UPLOAD_FOLDER'], event_name)
        os.makedirs(event_folder, exist_ok=True)

        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(event_folder)
        except (zipfile.BadZipFile, OSError):
            return jsonify({'error': 'Error extracting the zip file'}), 500

        try:
            for idx, extracted_file in enumerate(os.listdir(event_folder), start=1):
                extracted_file_path = os.path.join(event_folder, extracted_file)
                if os.path.isfile(extracted_file_path):
                    file_ext = os.path.splitext(extracted_file)[1]
                    new_filename = f"{event_name}_{idx}{file_ext}"
                    new_file_path = os.path.join(event_folder, new_filename)
                    os.rename(extracted_file_path, new_file_path)
        except OSError as e:
            print(e)
            return jsonify({'error': 'Error renaming the files'}), 500

        print("BEFORE MODEL")
        if await play.generate_event_embeddings(event_folder, event_name):
            print("BEFORE CLOUDINARY UPLOAD")

            cloudinary_result = await upload_to_cloudinary(event_folder, event_name)
            if cloudinary_result is not True:
                return jsonify({'error': f'Error uploading images to Cloudinary: {cloudinary_result}'}), 500

            try:
                shutil.rmtree(event_folder)
                os.remove(file_path)
            except OSError as e:
                return jsonify({'error': f'Error deleting local files: {str(e)}'}), 500

            return jsonify({'message': 'Event successfully added and files uploaded, processed, and cleaned up'}), 201
        else:
            return jsonify({'error': 'Error processing event embeddings'}), 500
    else:
        return jsonify({'error': 'Allowed file type is .zip'}), 400

@app.route('/my_events', methods=['POST'])
async def my_events():
    event_manager = request.json['event_manager_name']
    if event_manager == '':
        return jsonify({'error': 'Return Event_Manager Name'}), 400
    events = list(events_collection.find({'event_manager_name': event_manager}))
    for event in events:
        event['_id'] = str(event['_id'])
    return jsonify({'events': events}), 200