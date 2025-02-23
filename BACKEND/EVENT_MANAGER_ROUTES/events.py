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

# import asyncio
# import os
# import zipfile
# import shutil
# import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart



async def process_and_upload(event_folder, event_name, user_email):
    tasks = []
    urls = []

    async def process_file(file_path, new_file_name):
        # Generate embeddings asynchronously
        await play.generate_event_embeddings(file_path, new_file_name)
        
        # Upload file to GCS
        blob_name = f"upload_folder/{event_name}/{new_file_name}"
        blob = bucket.blob(blob_name)
        await asyncio.to_thread(blob.upload_from_filename, file_path)
        blob.make_public()
        urls.append(f"https://storage.googleapis.com/{bucket_name}/{blob_name}")
    
    try:
        for extracted_file in os.listdir(event_folder):
            extracted_file_path = os.path.join(event_folder, extracted_file)
            if not os.path.isfile(extracted_file_path):
                continue
            
            file_ext = os.path.splitext(extracted_file)[1]
            new_filename = f"{event_name}_{len(urls) + 1}{file_ext}"
            new_file_path = os.path.join(event_folder, new_filename)
            os.rename(extracted_file_path, new_file_path)
            
            tasks.append(process_file(new_file_path, new_filename))
        
        await asyncio.gather(*tasks)
        
        # Cleanup after processing
        shutil.rmtree(event_folder)
        send_email("kanavdhanda@hotmail.com", "Event Processing Complete", "Your event files have been processed and uploaded.")
    except Exception as e:
        send_email("kanavdhanda@hotmail.com", "Event Processing Failed", f"Error: {str(e)}")

def send_email(to_email, subject, body):
    sender_email = os.getenv("EMAIL_SENDER")
    sender_password = os.getenv("EMAIL_PASSWORD")
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Failed to send email: {e}")

@app.route('/add_new_event', methods=['POST'])
def add_new_event():
    event_manager_name = g.user['user_name']
    event_name = request.form['event_name']
    description = request.form['description']
    organized_by = request.form['organized_by']
    date = request.form['date']
    user_email = g.user['email']

    if not all([event_name, description, organized_by, date]):
        return jsonify({'error': 'All fields are required'}), 400

    if events_collection.find_one({'event_manager_name': event_manager_name, 'event_name': event_name}):
        return jsonify({'error': 'Event already exists'}), 400
    


    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.zip'):
        return jsonify({'error': 'Allowed file type is .zip'}), 400
    
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    file.save(file_path)
    
    event_folder = os.path.join(app.config['UPLOAD_FOLDER'], event_name)
    os.makedirs(event_folder, exist_ok=True)
    
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(event_folder)
    except (zipfile.BadZipFile, OSError):
        return jsonify({'error': 'Error extracting the zip file'}), 500
    
    asyncio.create_task(process_and_upload(event_folder, event_name, user_email))
    
    try:
        events_collection.insert_one({
            'event_manager_name': event_manager_name,
            'event_name': event_name,
            'description': description,
            'organized_by': organized_by,
            'date': date
        })
    except:
        return {'error': 'error in mongo'}, 500
    
    return jsonify({'message': 'Event registered. Processing will continue in the background.'}), 201

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
        events_collection.insert_one(event)
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
    print("BEFORE CLOUDINARY UPLOAD")
    tic_mid2 = time()
    print(tic_mid2-tic_mid)
    cloudinary_result, err = await upload_to_gcs(event_folder, event_name)
    # if cloudinary_result is not True:
    #     return jsonify({'error': f'Error uploading images to Cloudinary: {cloudinary_result}'}), 500
    if err:
        return jsonify({'error': f'Error while uploading images to GCS:{err}'}) , 500
    tic_end = time()
    print(tic_end-tic_mid2)
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