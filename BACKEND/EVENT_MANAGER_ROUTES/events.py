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
# import os
# import asyncio
# import shutil
# import zipfile
# from time import time
# from flask import Flask, request, jsonify, g
# from werkzeug.utils import secure_filename
# from google.cloud import storage

# app = Flask(__name__)
# app.config['UPLOAD_FOLDER'] = "uploads"  # Adjust as needed

# Google Cloud Storage Setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_PATH = os.path.join(BASE_DIR, "..", "config", "serviceAccount.json")
client = storage.Client.from_service_account_json(SERVICE_ACCOUNT_PATH)
bucket_name = "ccs-host.appspot.com"
bucket = client.bucket(bucket_name)

import os
import asyncio
import shutil
import zipfile
import smtplib
from email.mime.text import MIMEText
from time import time
from flask import Flask, request, jsonify, g
from werkzeug.utils import secure_filename
from google.cloud import storage

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "uploads"  # Adjust as needed

# Google Cloud Storage Setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_PATH = os.path.join(BASE_DIR, "..", "config", "serviceAccount.json")
client = storage.Client.from_service_account_json(SERVICE_ACCOUNT_PATH)
bucket_name = "ccs-host.appspot.com"
bucket = client.bucket(bucket_name)

async def upload_to_gcs(event_folder, event_name):
    try:
        urls = []
        tasks = []
        
        for image_file in os.listdir(event_folder):
            image_path = os.path.join(event_folder, image_file)
            if os.path.isfile(image_path):
                blob_name = f"upload_folder/{event_name}/{image_file}"
                blob = bucket.blob(blob_name)
                tasks.append(asyncio.to_thread(blob.upload_from_filename, image_path))
                urls.append(f"https://storage.googleapis.com/{bucket_name}/{blob_name}")
        
        await asyncio.gather(*tasks)
        
        # Make files public
        for blob_name in [url.replace(f"https://storage.googleapis.com/{bucket_name}/", "") for url in urls]:
            blob = bucket.blob(blob_name)
            blob.make_public()
        
        return urls, None
    except Exception as e:
        return None, str(e)

def send_email(recipient, subject, body):
    sender_email = os.getenv("EMAIL_SENDER")
    sender_password = os.getenv("EMAIL_PASSWORD")
    
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = recipient
    
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 587) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient, msg.as_string())
    except Exception as e:
        print(f"Error sending email: {e}")

async def process_embeddings_and_upload(event_folder, event_name):
    try:
        response = await asyncio.to_thread(play.generate_event_embeddings, event_folder, event_name)
        if not response:
            raise Exception("Error processing event embeddings")
        cloudinary_result, err = await upload_to_gcs(event_folder, event_name)
        if err:
            raise Exception(f"Error while uploading images to GCS: {err}")
        send_email("kanavdhanda@hotmail.com", "Event Processing Complete", f"Your event '{event_name}' has been processed and uploaded successfully.")
    finally:
        shutil.rmtree(event_folder)  # Cleanup

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
        if events_collection.find_one({'event_manager_name': event_manager_name, 'event_name': event_name}):
            return jsonify({'error': 'Event Already exists'}), 400
        events_collection.insert_one(event)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.zip'):
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

    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(event_folder)
    except (zipfile.BadZipFile, OSError):
        return jsonify({'error': 'Error extracting the zip file'}), 500

    for idx, extracted_file in enumerate(os.listdir(event_folder), start=1):
        extracted_file_path = os.path.join(event_folder, extracted_file)
        if not os.path.isfile(extracted_file_path):
            continue
        file_ext = os.path.splitext(extracted_file)[1]
        new_filename = f"{event_name}_{idx}{file_ext}"
        new_file_path = os.path.join(event_folder, new_filename)
        os.rename(extracted_file_path, new_file_path)
    
    asyncio.create_task(process_embeddings_and_upload(event_folder, event_name, recipient_email))
    os.remove(file_path)  # Remove zip file after extraction
    return jsonify({'message': 'Event added. Processing in background.'}), 202


@app.route('/my_events', methods=['POST'])
async def my_events():
    event_manager = g.user['user_name']
    if event_manager == '':
        return jsonify({'error': 'Return Event_Manager Name'}), 400
    events = list(events_collection.find({'event_manager_name': event_manager}))
    for event in events:
        event['_id'] = str(event['_id'])
    return jsonify({'events': events}), 200