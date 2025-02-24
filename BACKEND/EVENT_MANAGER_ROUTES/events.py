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
# from time import time
import time  # Make sure this is at the top

from datetime import datetime

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import aiofiles

# Upload to Google
from google.cloud import storage





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
bucket = client.bucket(os.getenv("bucket-name"))

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
#     """Handles large file uploads via streaming."""
#     try:
#         event_manager_name =request.headers.get('X-Event-Manager-Name')
#         event_name = request.headers.get('X-Event-Name')
#         description = request.headers.get('X-Description')
#         organized_by = request.headers.get('X-Organized-By')
#         date = request.headers.get('X-Date')

#         if not all([event_name, description, organized_by, date]):
#             return jsonify({'error': 'All fields are required'}), 400

#         event = {
#         'event_manager_name': event_manager_name,
#         'event_name': event_name,
#         'description': description,
#         'organized_by': organized_by,
#         'date': date
#         }


#         event_folder = os.path.join(app.config['UPLOAD_FOLDER'], event_name)
#         os.makedirs(event_folder, exist_ok=True)

#         file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{event_name}.zip")

#         # ✅ **Streaming file to disk correctly**
#         async with aiofiles.open(file_path, "wb") as f:
#             chunk_size=65536
#             while True:
#                 chunk = request.environ['wsgi.input'].read(chunk_size) # Read in 8KB chunks
#                 if not chunk:
#                     break
#                 await f.write(chunk)

#         # ✅ **Ensure file is completely written before extraction**
#         if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
#             return jsonify({'error': 'Uploaded file is empty or missing'}), 400

#         # ✅ **Extract zip file**
#         try:
#             def extract_zip(file_path, event_folder):
#                 with zipfile.ZipFile(file_path, 'r') as zip_ref:
#                     zip_ref.extractall(event_folder)

#             loop = asyncio.get_running_loop()
#             await loop.run_in_executor(None, extract_zip, file_path, event_folder)
#         except zipfile.BadZipFile:
#             return jsonify({'error': 'Invalid ZIP file'}), 400

#         # ✅ **Rename extracted files**
#         for idx, extracted_file in enumerate(os.listdir(event_folder), start=1):
#             extracted_file_path = os.path.join(event_folder, extracted_file)
#             if not os.path.isfile(extracted_file_path):
#                 continue
#             file_ext = os.path.splitext(extracted_file)[1]
#             new_filename = f"{event_name}_{idx}{file_ext}"
#             os.rename(extracted_file_path, os.path.join(event_folder, new_filename))


#         try:
#             if events_collection.find_one({'event_manager_name': event_manager_name, 'event_name': event_name}):
#                 return jsonify({'error': 'Event Already exists'}), 400
#             events_collection.insert_one(event)
#         except Exception as e:
#             return jsonify({'error': str(e)}), 400

#         # ✅ **Start background processing**

#         asyncio.create_task(process_embeddings_and_upload(event_folder, event_name))

#         os.remove(file_path)  # Delete zip file after extraction
#         return jsonify({'message': 'Event added. Processing in background.'}), 202
    
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500


# Initialize Flask app and Google Cloud Storage


def log_debug(message):
    """Utility function for consistent debug logging"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    print(f"[DEBUG {current_time}] {message}")


class BackgroundTaskManager:
    def __init__(self):
        self._tasks = set()
        log_debug("BackgroundTaskManager initialized")
    
    async def add_task(self, coro):
        log_debug(f"Adding new background task: {coro.__name__ if hasattr(coro, '__name__') else 'unnamed task'}")
        task = asyncio.create_task(self._task_wrapper(coro))
        self._tasks.add(task)
        log_debug(f"Current number of active tasks: {len(self._tasks)}")
        return task
    
    async def _task_wrapper(self, coro):
        try:
            log_debug(f"Starting background task execution")
            start_time = time.time()
            await coro
            execution_time = time.time() - start_time
            log_debug(f"Background task completed successfully in {execution_time:.2f} seconds")
        except Exception as e:
            log_debug(f"Background task failed with error: {str(e)}")
            raise
        finally:
            self._tasks.discard(asyncio.current_task())
            log_debug(f"Task removed from tracking. Remaining tasks: {len(self._tasks)}")

task_manager = BackgroundTaskManager()

async def upload_to_gcs(event_folder, event_name):
    """Upload files to Google Cloud Storage with improved concurrency."""
    try:
        log_debug(f"Starting GCS upload for event: {event_name}")
        urls = []
        upload_tasks = []
        bucket_name = bucket.name
        
        # Count files to upload
        files = [f for f in os.listdir(event_folder) if os.path.isfile(os.path.join(event_folder, f))]
        log_debug(f"Found {len(files)} files to upload in {event_folder}")

        # Prepare upload tasks
        for image_file in files:
            image_path = os.path.join(event_folder, image_file)
            blob_name = f"upload_folder/{event_name}/{image_file}"
            blob = bucket.blob(blob_name)
            
            log_debug(f"Preparing upload for file: {image_file}")
            upload_task = asyncio.create_task(
                asyncio.to_thread(blob.upload_from_filename, image_path)
            )
            upload_tasks.append(upload_task)
            urls.append(f"https://storage.googleapis.com/{bucket_name}/{blob_name}")

        # Wait for all uploads to complete
        log_debug(f"Starting concurrent upload of {len(upload_tasks)} files")
        start_time = time.time()
        await asyncio.gather(*upload_tasks)
        upload_time = time.time() - start_time
        log_debug(f"All files uploaded successfully in {upload_time:.2f} seconds")

        # Make files public concurrently
        log_debug("Making uploaded files public")
        public_tasks = []
        for url in urls:
            blob_name = url.replace(f"https://storage.googleapis.com/{bucket_name}/", "")
            blob = bucket.blob(blob_name)
            public_tasks.append(asyncio.to_thread(blob.make_public))
        
        await asyncio.gather(*public_tasks)
        log_debug("All files made public successfully")
        
        return urls, None
    except Exception as e:
        log_debug(f"Error in GCS upload: {str(e)}")
        return None, str(e)

async def send_email_async(to_email, subject, body):
    """Asynchronous email sending function."""
    try:
        log_debug(f"Preparing to send email to: {to_email}")
        sender_email = os.getenv("EMAIL_SENDER")
        sender_password = os.getenv("EMAIL_PASSWORD")
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        log_debug("Starting email send operation")
        await asyncio.to_thread(send_email_sync, msg, sender_email, sender_password, to_email)
        log_debug("Email sent successfully")
        return True
    except Exception as e:
        log_debug(f"Failed to send email: {str(e)}")
        return False

def send_email_sync(msg, sender_email, sender_password, to_email):
    """Synchronous email sending function."""
    log_debug("Establishing SMTP connection")
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
    log_debug("SMTP connection closed")

async def process_embeddings_and_upload(event_folder, event_name, email_receiver):
    """Background task to generate embeddings and upload files to GCS."""
    try:
        log_debug(f"Starting background processing for event: {event_name}")
        
        log_debug("Generating event embeddings")
        response = await play.generate_event_embeddings(event_folder, event_name)
        if not response:
            raise Exception("Error processing event embeddings")
        log_debug("Event embeddings generated successfully")
        
        log_debug("Starting file upload to GCS")
        urls, err = await upload_to_gcs(event_folder, event_name)
        if err:
            raise Exception(f"Error while uploading images to GCS: {err}")
        log_debug("Files uploaded successfully")
        
        log_debug("Sending success notification email")
        await send_email_async(
            email_receiver,
            "Event Processing Complete",
            f"Your event '{event_name}' has been processed and uploaded successfully.\nFile URLs:\n" + "\n".join(urls)
        )
    except Exception as e:
        log_debug(f"Error in background processing: {str(e)}")
        await send_email_async(
            "kanavdhanda@hotmail.com",
            "Event Processing Failed",
            f"Error processing event '{event_name}': {str(e)}"
        )
        raise
    finally:
        log_debug(f"Cleaning up event folder: {event_folder}")
        await asyncio.to_thread(shutil.rmtree, event_folder, ignore_errors=True)

# @app.route('/add_new_event', methods=['POST'])
# async def add_new_event():
#     """Handles large file uploads via streaming with improved error handling."""
#     event_folder = None
#     file_path = None
    
#     try:
#         log_debug("Received new event upload request")
        
#         # Validate headers
#         required_headers = {
#             'X-Event-Manager-Name': 'event_manager_name',
#             'X-Event-Name': 'event_name',
#             'X-Description': 'description',
#             'X-Organized-By': 'organized_by',
#             'X-Event-Manager-Email': 'event_manager_email',
#             'X-Date': 'date'
#         }
        
#         event = {}
#         for header, field in required_headers.items():
#             value = request.headers.get(header)
#             if not value:
#                 log_debug(f"Missing required header: {header}")
#                 return jsonify({'error': f'Missing required header: {header}'}), 400
#             event[field] = value

#         log_debug(f"Processing event: {event['event_name']}")

#         # Check for duplicate event
#         if events_collection.find_one({'event_manager_name': event['event_manager_name'], 
#                                      'event_name': event['event_name']}):
#             log_debug(f"Duplicate event found: {event['event_name']}")
#             return jsonify({'error': 'Event already exists'}), 400

#         # Create upload directory
#         event_folder = os.path.join(app.config['UPLOAD_FOLDER'], event['event_name'])
#         os.makedirs(event_folder, exist_ok=True)
#         log_debug(f"Created event folder: {event_folder}")
        
#         file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{event['event_name']}.zip")

#         # Stream file to disk
#         content_length = request.content_length
#         if not content_length:
#             log_debug("Missing Content-Length header")
#             return jsonify({'error': 'Content-Length header is required'}), 400
        
#         log_debug(f"Starting file upload, expected size: {content_length} bytes")
#         bytes_received = 0
#         chunk_size = 65536  # 64KB chunks
        
#         start_time = time.time()  # Using time.time() correctly now
        
#         async with aiofiles.open(file_path, "wb") as f:
#             while bytes_received < content_length:
#                 chunk = await asyncio.to_thread(
#                     request.environ['wsgi.input'].read,
#                     min(chunk_size, content_length - bytes_received)
#                 )
#                 if not chunk:
#                     break
#                 await f.write(chunk)
#                 bytes_received += len(chunk)
#                 if bytes_received % (1024 * 1024) == 0:  # Log every 1MB
#                     elapsed_time = time.time() - start_time
#                     upload_speed = bytes_received / (1024 * 1024 * elapsed_time)  # MB/s
#                     log_debug(f"Upload progress: {bytes_received}/{content_length} bytes ({(bytes_received/content_length)*100:.1f}%) - Speed: {upload_speed:.2f} MB/s")

#         upload_time = time.time() - start_time
#         final_speed = (bytes_received / (1024 * 1024)) / upload_time if upload_time > 0 else 0
#         log_debug(f"File upload completed in {upload_time:.2f} seconds. Average speed: {final_speed:.2f} MB/s")

#         if bytes_received != content_length:
#             raise ValueError(f"Incomplete file upload: got {bytes_received} bytes, expected {content_length}")

#         # Extract and rename files
#         log_debug("Starting file extraction and renaming")
#         await asyncio.to_thread(extract_and_rename_files, file_path, event_folder, event['event_name'])
        
#         # Save event to database
#         log_debug("Saving event to database")
#         await asyncio.to_thread(events_collection.insert_one, event)
        
#         # Start background processing
#         log_debug("Starting background processing task")
#         await task_manager.add_task(
#             process_embeddings_and_upload(event_folder, event['event_name'], event['event_manager_email'])
#         )
        
#         # Clean up zip file
#         if os.path.exists(file_path):
#             os.remove(file_path)
#             log_debug("Cleaned up temporary zip file")
        
#         log_debug("Event upload completed successfully")
#         return jsonify({
#             'message': 'Event added successfully. Processing in background.',
#             'event_name': event['event_name']
#         }), 202

#     except zipfile.BadZipFile:
#         log_debug("Invalid ZIP file uploaded")
#         return jsonify({'error': 'Invalid ZIP file'}), 400
#     except Exception as e:
#         log_debug(f"Error processing event upload: {str(e)}")
#         # Clean up on error
#         if file_path and os.path.exists(file_path):
#             os.remove(file_path)
#             log_debug("Cleaned up temporary zip file after error")
#         if event_folder and os.path.exists(event_folder):
#             shutil.rmtree(event_folder, ignore_errors=True)
#             log_debug("Cleaned up event folder after error")
#         return jsonify({'error': str(e)}), 500

# async def add_new_event():
#     """Handles large file uploads via streaming with improved error handling."""
#     event_folder = None
#     file_path = None
    
#     try:
#         log_debug("Received new event upload request")
        
#         # Validate headers
#         required_headers = {
#             'X-Event-Manager-Name': 'event_manager_name',
#             'X-Event-Name': 'event_name',
#             'X-Description': 'description',
#             'X-Organized-By': 'organized_by',
#             'X-Date': 'date'
#         }
        
#         event = {}
#         for header, field in required_headers.items():
#             value = request.headers.get(header)
#             if not value:
#                 log_debug(f"Missing required header: {header}")
#                 return jsonify({'error': f'Missing required header: {header}'}), 400
#             event[field] = value

#         log_debug(f"Processing event: {event['event_name']}")

#         # Check for duplicate event
#         if events_collection.find_one({'event_manager_name': event['event_manager_name'], 
#                                      'event_name': event['event_name']}):
#             log_debug(f"Duplicate event found: {event['event_name']}")
#             return jsonify({'error': 'Event already exists'}), 400

#         # Create upload directory
#         event_folder = os.path.join(app.config['UPLOAD_FOLDER'], event['event_name'])
#         os.makedirs(event_folder, exist_ok=True)
#         log_debug(f"Created event folder: {event_folder}")
        
#         file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{event['event_name']}.zip")

#         # Stream file to disk
#         content_length = request.content_length
#         if not content_length:
#             log_debug("Missing Content-Length header")
#             return jsonify({'error': 'Content-Length header is required'}), 400
        
#         log_debug(f"Starting file upload, expected size: {content_length} bytes")
#         bytes_received = 0
#         chunk_size = 65536  # 64KB chunks
        
#         start_time = time.time()
#         async with aiofiles.open(file_path, "wb") as f:
#             while bytes_received < content_length:
#                 chunk = await asyncio.to_thread(
#                     request.environ['wsgi.input'].read,
#                     min(chunk_size, content_length - bytes_received)
#                 )
#                 if not chunk:
#                     break
#                 await f.write(chunk)
#                 bytes_received += len(chunk)
#                 if bytes_received % (1024 * 1024) == 0:  # Log every 1MB
#                     log_debug(f"Upload progress: {bytes_received}/{content_length} bytes ({(bytes_received/content_length)*100:.1f}%)")

#         upload_time = time.time() - start_time
#         log_debug(f"File upload completed in {upload_time:.2f} seconds")

#         if bytes_received != content_length:
#             raise ValueError(f"Incomplete file upload: got {bytes_received} bytes, expected {content_length}")

#         # Extract and rename files
#         log_debug("Starting file extraction and renaming")
#         await asyncio.to_thread(extract_and_rename_files, file_path, event_folder, event['event_name'])
        
#         # Save event to database
#         log_debug("Saving event to database")
#         await asyncio.to_thread(events_collection.insert_one, event)
        
#         # Start background processing
#         log_debug("Starting background processing task")
#         await task_manager.add_task(
#             process_embeddings_and_upload(event_folder, event['event_name'])
#         )
        
#         # Clean up zip file
#         if os.path.exists(file_path):
#             os.remove(file_path)
#             log_debug("Cleaned up temporary zip file")
        
#         log_debug("Event upload completed successfully")
#         return jsonify({
#             'message': 'Event added successfully. Processing in background.',
#             'event_name': event['event_name']
#         }), 202

#     except zipfile.BadZipFile:
#         log_debug("Invalid ZIP file uploaded")
#         return jsonify({'error': 'Invalid ZIP file'}), 400
#     except Exception as e:
#         log_debug(f"Error processing event upload: {str(e)}")
#         # Clean up on error
#         if file_path and os.path.exists(file_path):
#             os.remove(file_path)
#             log_debug("Cleaned up temporary zip file after error")
#         if event_folder and os.path.exists(event_folder):
#             shutil.rmtree(event_folder, ignore_errors=True)
#             log_debug("Cleaned up event folder after error")
#         return jsonify({'error': str(e)}), 500




CHUNK_FOLDER = os.path.join(app.config['UPLOAD_FOLDER'], "chunks")

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(CHUNK_FOLDER, exist_ok=True)


@app.route("/upload_chunk", methods=["POST"])
async def upload_chunk():
    """Handles chunked file uploads."""
    chunk = request.files.get("chunk")
    chunk_index = request.form.get("chunk_index", type=int)
    total_chunks = request.form.get("total_chunks", type=int)
    file_name = request.form.get("file_name")

    if not chunk or chunk_index is None or total_chunks is None or not file_name:
        return jsonify({"error": "Invalid chunk data"}), 400

    chunk_path = os.path.join(CHUNK_FOLDER, f"{file_name}.part{chunk_index}")

    async with aiofiles.open(chunk_path, "wb") as f:
        await f.write(chunk.read())

    return jsonify({"message": f"Chunk {chunk_index}/{total_chunks} received"}), 200


@app.route("/finalize_upload", methods=["POST"])
async def finalize_upload():
    """Assembles uploaded chunks and processes the file."""
    data = request.json
    file_name = data.get("file_name")
    event_data = data.get("eventData")

    if not file_name or not event_data:
        return jsonify({"error": "Missing required parameters"}), 400

    final_path = os.path.join(UPLOAD_FOLDER, file_name)
    
    # Assemble the chunks
    chunk_paths = sorted(
        [os.path.join(CHUNK_FOLDER, f) for f in os.listdir(CHUNK_FOLDER) if f.startswith(file_name)],
        key=lambda x: int(x.split(".part")[-1])
    )

    async with aiofiles.open(final_path, "wb") as final_file:
        for chunk_path in chunk_paths:
            async with aiofiles.open(chunk_path, "rb") as chunk_file:
                await final_file.write(await chunk_file.read())
            os.remove(chunk_path)  # Clean up chunk file

    # Verify zip integrity
    if not zipfile.is_zipfile(final_path):
        os.remove(final_path)
        return jsonify({"error": "Invalid ZIP file"}), 400

    # Extract and process the event
    event_folder = os.path.join(UPLOAD_FOLDER, event_data["event_name"])
    os.makedirs(event_folder, exist_ok=True)

    await asyncio.to_thread(extract_and_rename_files, final_path, event_folder, event_data["event_name"])

    # Clean up original zip
    os.remove(final_path)

    return jsonify({"message": "File uploaded and processed successfully"}), 200


def extract_and_rename_files(file_path, event_folder, event_name):
    """Extract zip file and rename files in one function to reduce complexity."""
    try:
        log_debug(f"Extracting zip file: {file_path}")
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(event_folder)
        log_debug("Zip file extracted successfully")
        
        # Rename files
        files = os.listdir(event_folder)
        log_debug(f"Renaming {len(files)} extracted files")
        
        for idx, extracted_file in enumerate(files, start=1):
            extracted_file_path = os.path.join(event_folder, extracted_file)
            if not os.path.isfile(extracted_file_path):
                continue
            file_ext = os.path.splitext(extracted_file)[1]
            new_filename = f"{event_name}_{idx}{file_ext}"
            new_path = os.path.join(event_folder, new_filename)
            os.rename(extracted_file_path, new_path)
            log_debug(f"Renamed: {extracted_file} -> {new_filename}")
        
        log_debug("File extraction and renaming completed")
    except Exception as e:
        log_debug(f"Error in extract_and_rename_files: {str(e)}")
        raise
@app.route('/my_events', methods=['POST'])
async def my_events():
    event_manager = g.user['user_name']
    if event_manager == '':
        return jsonify({'error': 'Return Event_Manager Name'}), 400
    events = list(events_collection.find({'event_manager_name': event_manager}))
    for event in events:
        event['_id'] = str(event['_id'])
    return jsonify({'events': events}), 200