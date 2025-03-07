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

from datetime import datetime, timedelta  # Include datetime if you need it too

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import aiofiles

# Upload to Google
from google.cloud import storage
import hashlib

from bson.objectid import ObjectId



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
        log_debug("Sending Start notification email")
        await send_email_async(
            email_receiver,
            "Event Processing Started",
            f"Your event '{event_name}' has started processing and embeddings are now being"
        )
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




# Constants
CHUNK_SIZE = 5 * 1024 * 1024  # 5MB chunks
UPLOAD_EXPIRY_HOURS = 24
CONCURRENT_CHUNKS = 3

# class UploadSession:
#     def __init__(self, total_size, file_id, metadata, chunks):
#         self.total_size = total_size
#         self.file_id = file_id
#         self.metadata = metadata
#         self.received_chunks = set()
#         self.expected_chunks = chunks
#         self.created_at = datetime.now()
#         self.temp_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'temp', file_id)
#         self.is_finalized = False  # New flag to track if finalization was requested
#         os.makedirs(self.temp_dir, exist_ok=True)

#     def is_expired(self):
#         return datetime.now() - self.created_at > timedelta(hours=UPLOAD_EXPIRY_HOURS)

#     def is_complete(self):
#         """Check if all chunks have been received"""
#         return len(self.received_chunks) == self.expected_chunks
class UploadSession:
    def __init__(self, total_size, file_id, metadata, chunks):
        self.total_size = total_size
        self.file_id = file_id
        self.metadata = metadata
        self.received_chunks = set()
        self.expected_chunks = chunks
        self.created_at = datetime.now()
        self.temp_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'temp', file_id)
        self.is_finalized = False
        os.makedirs(self.temp_dir, exist_ok=True)

    def is_expired(self):
        return datetime.now() - self.created_at > timedelta(hours=UPLOAD_EXPIRY_HOURS)

    def is_complete(self):
        """Check if all chunks have been received"""
        return len(self.received_chunks) == self.expected_chunks


async def process_upload_background(session):
    """Background task to reassemble chunks and process the upload"""
    try:
        log_debug(f"Starting background processing for file ID: {session.file_id}")
        
        # Create final file path
        file_name = session.metadata['file_name']
        final_file_path = os.path.join(app.config['UPLOAD_FOLDER'], session.file_id + '_' + file_name)
        
        # Create a new file to hold the reassembled chunks
        async with aiofiles.open(final_file_path, 'wb') as output_file:
            # Process chunks in order
            for chunk_index in range(session.expected_chunks):
                chunk_path = os.path.join(session.temp_dir, f'chunk_{chunk_index}')
                
                if not os.path.exists(chunk_path):
                    raise FileNotFoundError(f"Missing chunk {chunk_index} at {chunk_path}")
                
                # Read the chunk and write to the output file
                async with aiofiles.open(chunk_path, 'rb') as chunk_file:
                    chunk_data = await chunk_file.read()
                    await output_file.write(chunk_data)
        
        log_debug(f"File reassembly complete: {final_file_path}")

        # Verify the file size matches the expected total
        file_stats = os.stat(final_file_path)
        if file_stats.st_size != session.total_size:
            log_debug(f"Warning: Reassembled file size {file_stats.st_size} does not match expected size {session.total_size}")
            
        # Store event metadata in database
        event_data = {
            'file_id': session.file_id,
            'file_path': final_file_path,
            'file_name': session.metadata['file_name'],
            'event_name': session.metadata['event_name'],
            'organized_by': session.metadata['organized_by'],
            'description': session.metadata['description'],
            'event_manager_name': session.metadata['event_manager_name'],
            'event_manager_email': session.metadata['event_manager_email'],
            'date': session.metadata['date'],
            'upload_date': datetime.now(),
            'file_size': file_stats.st_size
        }
        
        events_collection.insert_one(event_data)
        log_debug(f"Event metadata stored in database for {session.metadata['event_name']}")
        

        try:
            await process_complete_upload(session)
        finally:
            cleanup_session(session.file_id)

        
    except Exception as e:
        log_debug(f"Error in background processing: {str(e)}")
        # Keep session for debugging
        # Don't remove: cleanup_session(session.file_id)


def cleanup_session(file_id):
    """Clean up temporary files and remove session"""
    try:
        session = upload_sessions.get(file_id)
        if session:
            # Delete all temporary chunk files
            for chunk_index in range(session.expected_chunks):
                chunk_path = os.path.join(session.temp_dir, f'chunk_{chunk_index}')
                if os.path.exists(chunk_path):
                    os.remove(chunk_path)
            
            # Remove temp directory
            if os.path.exists(session.temp_dir):
                os.rmdir(session.temp_dir)
            
            # Remove session from memory
            del upload_sessions[file_id]
            log_debug(f"Cleaned up session {file_id}")
    except Exception as e:
        log_debug(f"Error cleaning up session {file_id}: {str(e)}")
# In-memory storage for upload sessions
upload_sessions = {}

@app.route('/init_upload', methods=['POST'])
async def init_upload():
    """Initialize a new chunked upload session"""
    try:
        # Validate request
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400

        data = request.get_json()
        required_fields = {
            'totalSize': 'total_size',
            'fileName': 'file_name',
            'eventName': 'event_name',
            'organizedBy': 'organized_by',
            'description': 'description',
            'eventManagerName': 'event_manager_name',
            'eventManagerEmail': 'event_manager_email',
            'totalChunks': 'chunks',
            'date': 'date'
        }

        metadata = {}
        for field, key in required_fields.items():
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
            metadata[key] = data[field]
        chunks = metadata['chunks']
        print(chunks)
        # Generate unique file ID
        file_id = hashlib.sha256(f"{metadata['event_name']}_{metadata['file_name']}_{datetime.now().isoformat()}".encode()).hexdigest()

        # Check for duplicate event
        if events_collection.find_one({
            # 'event_manager_name': metadata['event_manager_name'],
            'event_name': metadata['event_name']
        }):
            return jsonify({'error': 'Event already exists'}), 400

        # Create upload session
        session = UploadSession(
            total_size=data['totalSize'],
            file_id=file_id,
            metadata=metadata,
            chunks=chunks
        )
        upload_sessions[file_id] = session

        return jsonify({
            'fileId': file_id,
            'chunkSize': CHUNK_SIZE,
            'totalChunks': (data['totalSize'] + CHUNK_SIZE - 1) // CHUNK_SIZE,
            'expiresIn': UPLOAD_EXPIRY_HOURS * 3600  # seconds
        }), 200

    except Exception as e:
        log_debug(f"Error initializing upload: {str(e)}")
        return jsonify({'error': str(e)}), 500



@app.route('/upload_chunk/<file_id>', methods=['POST'])
async def upload_chunk(file_id):
    try:
        if file_id not in upload_sessions:
            return jsonify({"error": "Invalid file ID"}), 400

        session = upload_sessions[file_id]
        chunk_index = int(request.headers.get('X-Chunk-Index', -1))

        if chunk_index < 0 or chunk_index >= session.expected_chunks:
            return jsonify({"error": "Invalid chunk index"}), 400

        if chunk_index in session.received_chunks:
            return jsonify({'message': 'Chunk already received', 'chunkIndex': chunk_index}), 200

        chunk_data = request.get_data()
        if not chunk_data:
            return jsonify({'error': 'Empty chunk received'}), 400

        chunk_file = os.path.join(session.temp_dir, f'chunk_{chunk_index}')

        async with aiofiles.open(chunk_file, 'wb') as f:
            await f.write(chunk_data)
        session.received_chunks.add(chunk_index)

        return jsonify({
            'message': 'Chunk received',
            'chunkIndex': chunk_index,
            'remainingChunks': session.expected_chunks - len(session.received_chunks),
            'allChunksReceived': session.is_complete()
        }), 200

    except Exception as e:
        log_debug(f"Error uploading chunk: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Add a new route for finalizing the upload
@app.route('/verify_upload/<file_id>', methods=['POST'])
async def verify_upload(file_id):
    """Verify that an upload is complete but don't process it yet"""
    try:
        session = upload_sessions.get(file_id)
        if not session:
            return jsonify({'error': 'Upload session not found'}), 404

        if session.is_expired():
            cleanup_session(file_id)
            return jsonify({'error': 'Upload session expired'}), 410

        if not session.is_complete():
            missing = session.expected_chunks - len(session.received_chunks)
            return jsonify({
                'error': f'Upload incomplete. Missing {missing} chunks.',
                'receivedChunks': len(session.received_chunks),
                'expectedChunks': session.expected_chunks
            }), 400
            
        return jsonify({
            'message': 'Upload verification successful',
            'fileId': session.file_id,
            'event_name': session.metadata['event_name'],
            'totalChunks': session.expected_chunks,
            'receivedChunks': len(session.received_chunks)
        }), 200

    except Exception as e:
        log_debug(f"Error verifying upload: {str(e)}")
        return jsonify({'error': str(e)}), 500


# Completely separate route for processing
@app.route('/process_upload/<file_id>', methods=['POST'])
async def process_upload(file_id):
    """Process a completed upload"""
    try:
        session = upload_sessions.get(file_id)
        if not session:
            return jsonify({'error': 'Upload session not found'}), 404

        if session.is_expired():
            cleanup_session(file_id)
            return jsonify({'error': 'Upload session expired'}), 410

        if not session.is_complete():
            missing = session.expected_chunks - len(session.received_chunks)
            return jsonify({
                'error': f'Upload incomplete. Missing {missing} chunks.',
                'receivedChunks': len(session.received_chunks),
                'expectedChunks': session.expected_chunks
            }), 400
            
        if session.is_finalized:
            return jsonify({'message': 'Upload already processed'}), 200
            
        session.is_finalized = True
        
        # Start a background task to process the upload
        asyncio.create_task(process_upload_background(session))
        
        return jsonify({
            'message': 'Upload processing started',
            'event_name': session.metadata['event_name']
        }), 202

    except Exception as e:
        log_debug(f"Error processing upload: {str(e)}")
        return jsonify({'error': str(e)}), 500


# async def process_upload_background(session):
#     """Background task to process the upload"""
#     try:
#         await process_complete_upload(session)
#     finally:
#         cleanup_session(session.file_id)



async def process_complete_upload(session):
    """Process a completed upload"""
    try:
        # Combine chunks into final file
        upload_folder = app.config['UPLOAD_FOLDER']
        final_path = os.path.join(upload_folder, f"{session.metadata['event_name']}.zip")
        
        log_debug(f"Final zip path: {final_path}")
        
        async with aiofiles.open(final_path, 'wb') as outfile:
            for i in range(len(session.received_chunks)):
                chunk_path = os.path.join(session.temp_dir, f'chunk_{i}')
                if not os.path.exists(chunk_path):
                    log_debug(f"Missing chunk: {chunk_path}")
                    continue
                try:
                    async with aiofiles.open(chunk_path, 'rb') as chunk_file:
                        chunk_data = await chunk_file.read()
                        if not chunk_data:
                            log_debug(f"Empty chunk: {chunk_path}")
                            continue
                        await outfile.write(chunk_data)
                except Exception as chunk_error:
                    log_debug(f"Error reading chunk {chunk_path}: {chunk_error}")
                    continue
        
        # Create event folder
        event_folder = os.path.join(upload_folder, session.metadata['event_name'])
        log_debug(f"Event folder path: {event_folder}")
        os.makedirs(event_folder, exist_ok=True)
        
        # Extract and process files
        await asyncio.to_thread(extract_and_rename_files, final_path, event_folder, session.metadata['event_name'])
        
        # Store metadata
        await asyncio.to_thread(events_collection.insert_one, session.metadata)
        
        # Start background processing
        await task_manager.add_task(
            process_embeddings_and_upload(
                event_folder,
                session.metadata['event_name'],
                session.metadata['event_manager_email']
            )
        )
        
        # Cleanup
        os.remove(final_path)
    except Exception as e:
        log_debug(f"Error processing complete upload: {str(e)}")


def extract_and_rename_files(file_path, event_folder, event_name):
    """Extract zip file, rename images, and delete non-image files."""
    try:
        if not os.path.exists(event_folder):
            os.makedirs(event_folder)

        log_debug(f"Extracting zip file: {file_path}")
        
        # Extract files
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(event_folder)
        
        log_debug("Zip file extracted successfully")
        
        # Define allowed image extensions
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
        
        # Ensure all extracted files are counted correctly
        extracted_files = []
        for root, _, files in os.walk(event_folder):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.splitext(file)[1].lower() in allowed_extensions:
                    extracted_files.append(file_path)
                else:
                    os.remove(file_path)  # Delete non-image files
                    log_debug(f"Deleted non-image file: {file_path}")
        
        log_debug(f"Renaming {len(extracted_files)} extracted image files")
        
        for idx, extracted_file_path in enumerate(extracted_files, start=1):
            file_ext = os.path.splitext(extracted_file_path)[1]
            new_filename = f"{event_name}_{idx}{file_ext}"
            new_path = os.path.join(event_folder, new_filename)
            
            os.rename(extracted_file_path, new_path)
            log_debug(f"Renamed: {os.path.basename(extracted_file_path)} -> {new_filename}")
        
        log_debug("File extraction, cleanup, and renaming completed")
    except Exception as e:
        log_debug(f"Error in extract_and_rename_files: {str(e)}")
        raise


def cleanup_session(file_id):
    """Clean up upload session and temporary"""
    session = upload_sessions.pop(file_id, None)
    if session and os.path.exists(session.temp_dir):
        shutil.rmtree(session.temp_dir, ignore_errors=True)







@app.route('/my_events', methods=['POST'])
async def my_events():
    event_manager = g.user['user_name']
    if event_manager == '':
        return jsonify({'error': 'Return Event_Manager Name'}), 400
    events = list(events_collection.find({'event_manager_name': event_manager}))
    for event in events:
        event['_id'] = str(event['_id'])
    return jsonify({'events': events}), 200

@app.route('/events/<event_id>', methods=['DELETE'])
async def delete_event(event_id):
    event_manager = g.user.get('user_name', '')

    if not event_manager:
        return jsonify({'error': 'Return Event_Manager Name'}), 400

    # Validate ObjectId format
    if not ObjectId.is_valid(event_id):
        return jsonify({'error': 'Invalid Event ID'}), 400

    event_obj_id = ObjectId(event_id)
    
    # Check if the event exists
    event = events_collection.find_one({'_id': event_obj_id})
    if not event:
        return jsonify({'error': 'Event not found'}), 404

    # Delete the event
    result = events_collection.delete_one({'_id': event_obj_id})

    if result.deleted_count == 1:
        return jsonify({'message': 'Event deleted successfully'}), 200
    else:
        return jsonify({'error': 'Failed to delete event'}), 500
