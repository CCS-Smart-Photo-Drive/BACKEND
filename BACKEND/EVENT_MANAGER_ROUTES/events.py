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

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import aiofiles

# Upload to Google
from google.cloud import storage
import asyncio
import os
import concurrent.futures



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

# import os
# import asyncio
# import shutil
# import zipfile





# async def upload_to_gcs(event_folder, event_name):
#     try:
#         urls = []
#         tasks = []
        
#         for image_file in os.listdir(event_folder):
#             image_path = os.path.join(event_folder, image_file)
#             if os.path.isfile(image_path):
#                 blob_name = f"upload_folder/{event_name}/{image_file}"
#                 blob = bucket.blob(blob_name)
#                 tasks.append(asyncio.to_thread(blob.upload_from_filename, image_path))
#                 urls.append(f"https://storage.googleapis.com/{bucket_name}/{blob_name}")
        
#         await asyncio.gather(*tasks)
        
#         # Make files public
#         for blob_name in [url.replace(f"https://storage.googleapis.com/{bucket_name}/", "") for url in urls]:
#             blob = bucket.blob(blob_name)
#             blob.make_public()
        
#         return urls, None
#     except Exception as e:
#         return None, str(e)

# def send_email(to_email, subject, body):
#     sender_email = os.getenv("EMAIL_SENDER")
#     sender_password = os.getenv("EMAIL_PASSWORD")
    
#     msg = MIMEMultipart()
#     msg['From'] = sender_email
#     msg['To'] = to_email
#     msg['Subject'] = subject
#     msg.attach(MIMEText(body, 'plain'))
    
#     try:
#         server = smtplib.SMTP('smtp.gmail.com', 587)
#         server.starttls()
#         server.login(sender_email, sender_password)
#         server.sendmail(sender_email, to_email, msg.as_string())
#         server.quit()
#     except Exception as e:
#         print(f"Failed to send email: {e}")

# async def process_embeddings_and_upload(event_folder, event_name):
#     """Background task to generate embeddings and upload files to GCS."""
#     try:
#         response = await play.generate_event_embeddings(event_folder, event_name)
#         if not response:
#             raise Exception("Error processing event embeddings")
        
#         urls, err = await upload_to_gcs(event_folder, event_name)
#         if err:
#             raise Exception(f"Error while uploading images to GCS: {err}")
#         send_email(
#             "kanavdhanda@hotmail.com",
#             "Event Processing Complete",
#         f"Your event '{event_name}' has been processed and uploaded successfully.\nFile URLs:\n" + "\n".join(urls)
#         )
#     finally:
#         shutil.rmtree(event_folder)  # Cleanup


# @app.route('/add_new_event', methods=['POST'])
# async def add_new_event():
    # """Handles large file uploads via streaming."""
    # try:
    #     event_manager_name =request.headers.get('X-Event-Manager-Name')
    #     event_name = request.headers.get('X-Event-Name')
    #     description = request.headers.get('X-Description')
    #     organized_by = request.headers.get('X-Organized-By')
    #     date = request.headers.get('X-Date')

    #     if not all([event_name, description, organized_by, date]):
    #         return jsonify({'error': 'All fields are required'}), 400

    #     event = {
    #     'event_manager_name': event_manager_name,
    #     'event_name': event_name,
    #     'description': description,
    #     'organized_by': organized_by,
    #     'date': date
    #     }


    #     event_folder = os.path.join(app.config['UPLOAD_FOLDER'], event_name)
    #     os.makedirs(event_folder, exist_ok=True)

    #     file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{event_name}.zip")

    #     # ✅ **Streaming file to disk correctly**
    #     async with aiofiles.open(file_path, "wb") as f:
    #         chunk_size=65536
    #         while True:
    #             chunk = request.environ['wsgi.input'].read(chunk_size) # Read in 8KB chunks
    #             if not chunk:
    #                 break
    #             await f.write(chunk)

    #     # ✅ **Ensure file is completely written before extraction**
    #     if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
    #         return jsonify({'error': 'Uploaded file is empty or missing'}), 400

    #     # ✅ **Extract zip file**
    #     try:
    #         def extract_zip(file_path, event_folder):
    #             with zipfile.ZipFile(file_path, 'r') as zip_ref:
    #                 zip_ref.extractall(event_folder)

    #         loop = asyncio.get_running_loop()
    #         await loop.run_in_executor(None, extract_zip, file_path, event_folder)
    #     except zipfile.BadZipFile:
    #         return jsonify({'error': 'Invalid ZIP file'}), 400

    #     # ✅ **Rename extracted files**
    #     for idx, extracted_file in enumerate(os.listdir(event_folder), start=1):
    #         extracted_file_path = os.path.join(event_folder, extracted_file)
    #         if not os.path.isfile(extracted_file_path):
    #             continue
    #         file_ext = os.path.splitext(extracted_file)[1]
    #         new_filename = f"{event_name}_{idx}{file_ext}"
    #         os.rename(extracted_file_path, os.path.join(event_folder, new_filename))


    #     try:
    #         if events_collection.find_one({'event_manager_name': event_manager_name, 'event_name': event_name}):
    #             return jsonify({'error': 'Event Already exists'}), 400
    #         events_collection.insert_one(event)
    #     except Exception as e:
    #         return jsonify({'error': str(e)}), 400

    #     # ✅ **Start background processing**

    #     asyncio.create_task(process_embeddings_and_upload(event_folder, event_name))

    #     os.remove(file_path)  # Delete zip file after extraction
    #     return jsonify({'message': 'Event added. Processing in background.'}), 202
    
    # except Exception as e:
    #     return jsonify({'error': str(e)}), 500

@app.route('/my_events', methods=['POST'])
async def my_events():
    event_manager = g.user['user_name']
    if event_manager == '':
        return jsonify({'error': 'Return Event_Manager Name'}), 400
    events = list(events_collection.find({'event_manager_name': event_manager}))
    for event in events:
        event['_id'] = str(event['_id'])
    return jsonify({'events': events}), 200


async def save_uploaded_files(upload_dir, files):
    """Save uploaded files asynchronously and ensure they are fully written."""
    os.makedirs(upload_dir, exist_ok=True)
    saved_files = []
    
    for file in files:
        file_path = os.path.join(upload_dir, file.filename)
        try:
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(await file.read())  # Fully write file
            saved_files.append(file_path)
        except Exception as e:
            print(f"Failed to save file {file.filename}: {e}")

    return saved_files


@app.route('/add_new_event', methods=['POST'])
async def add_new_event():
    """Handles event file upload and triggers processing."""
    event_name = request.form.get("event_name")
    if not event_name:
        return jsonify({"error": "Event name is required"}), 400

    event_folder = os.path.join("uploads", event_name)

    # Save files
    files = await save_uploaded_files(event_folder, request.files.getlist("files"))

    if not files:
        return jsonify({"error": "No files uploaded"}), 400

    # Trigger background processing
    asyncio.create_task(process_embeddings_and_upload(event_folder, event_name))

    return jsonify({"message": "Event is being processed"}), 202


async def process_embeddings_and_upload(event_folder, event_name):
    """Background task to generate embeddings and upload files to GCS."""
    try:
        await asyncio.sleep(2)  # Ensure files are fully saved

        if not os.listdir(event_folder):
            raise Exception("No files found for embeddings")

        print(f"Generating embeddings for event: {event_name}")
        response = await play.generate_event_embeddings(event_folder, event_name)
        if not response:
            raise Exception("Error processing event embeddings")

        urls, err = await upload_to_gcs(event_folder, event_name)
        if err:
            raise Exception(f"Error while uploading images to GCS: {err}")

        print(f"Successfully processed event '{event_name}'. Sending email...")
        send_email(
            "kanavdhanda@hotmail.com",
            "Event Processing Complete",
            f"Your event '{event_name}' has been processed and uploaded successfully.\nFile URLs:\n" + "\n".join(urls)
        )

    except Exception as e:
        print(f"Error processing event '{event_name}': {e}")

    finally:
        shutil.rmtree(event_folder)  # Cleanup


async def upload_to_gcs(event_folder, event_name):
    """Uploads images to Google Cloud Storage."""
    try:
        urls = []
        tasks = []

        for image_file in os.listdir(event_folder):
            image_path = os.path.join(event_folder, image_file)
            if os.path.isfile(image_path):
                blob_name = f"upload_folder/{event_name}/{image_file}"
                blob = bucket.blob(blob_name)

                # Upload asynchronously
                tasks.append(asyncio.to_thread(blob.upload_from_filename, image_path))
                urls.append(f"https://storage.googleapis.com/{bucket_name}/{blob_name}")

        await asyncio.gather(*tasks)

        # Make files public
        for blob_name in [url.replace(f"https://storage.googleapis.com/{bucket_name}/", "") for url in urls]:
            blob = bucket.blob(blob_name)
            blob.make_public()

        print(f"Uploaded {len(urls)} files to GCS for event '{event_name}'")
        return urls, None

    except Exception as e:
        print(f"Failed to upload files to GCS: {e}")
        return None, str(e)


def send_email(to_email, subject, body):
    """Sends an email using a secure SMTP connection."""
    sender_email = os.getenv("EMAIL_SENDER")
    sender_password = os.getenv("EMAIL_PASSWORD")  # Use an App Password

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())

        print(f"Email sent successfully to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")
