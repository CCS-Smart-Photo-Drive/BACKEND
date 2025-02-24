import os
import zipfile
import shutil
import uuid

from flask import  request, jsonify, send_file, g
from werkzeug.utils import secure_filename
import bcrypt
from BACKEND.init_config import user_collection, app, events_collection
from FACE_MODEL.play import generate_user_embeddings, finding_nemo
import requests
import asyncio
# Upload to Google
from google.cloud import storage
import asyncio

#
# @app.route('/my_dashboard', methods=['POST'])
# async def user_my_dashboard():
#     user_name = g.user['user_name']
#     user_email = g.user['email']
#     if 'user_file' not in request.files:
#         return jsonify({'error': 'No file part'}), 400
#
#     user_dp = request.files['user_file']
#     if user_dp.filename == '':
#         return jsonify({'error': 'No file selected for uploading'}), 400
#
#     try:
#         filename = secure_filename(user_dp.filename)
#         file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#         os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
#         user_dp.save(file_path)
#         print("yes1")
#         if generate_user_embeddings(file_path, user_email,  user_name):
#             await asyncio.to_thread(cloudinary.uploader.upload, file_path, folder = "MY_USERS", public_id=g.user['email'])
#         print("yes2")
#         # await asyncio.gather(task)
#
#
#
#         os.remove(file_path)
#
#         return jsonify({'message': 'User dashboard updated successfully'}), 200
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500



# Initialize Google Cloud Storage Client with Service Account
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Directory of this script
SERVICE_ACCOUNT_PATH = os.path.join(BASE_DIR, "..", "config", "serviceAccount.json")

# Initialize the client
client = storage.Client.from_service_account_json(SERVICE_ACCOUNT_PATH)
bucket_name = "ccs-host.appspot.com"
bucket = client.bucket(bucket_name)

async def upload_to_gcs(local_file_path, user_email):
    try:
        # Generate a random filename
        ext = os.path.splitext(local_file_path)[1]
        random_filename = f"profile_{uuid.uuid4().hex}{ext}"

        # Define blob path
        blob_name = f"upload_folder/users/{user_email}/{random_filename}"
        blob = bucket.blob(blob_name)

        # Asynchronous upload
        await asyncio.to_thread(blob.upload_from_filename, local_file_path)

        # Make the file public
        blob.make_public()
        print(blob.public_url)
        # Return public URL
        return blob.public_url, None

    except Exception as e:
        return None, str(e)

@app.route('/my_dashboard', methods=['POST'])
async def user_my_dashboard():
    user_name = g.user['user_name']
    user_email = g.user['email']

    if 'user_file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    user_dp = request.files['user_file']
    if user_dp.filename == '':
        return jsonify({'error': 'No file selected for uploading'}), 400

    try:
        filename = secure_filename(user_dp.filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save the file locally
        user_dp.save(file_path)
        embedGen = generate_user_embeddings(file_path, user_email, user_name)
        print(embedGen)
        # Process embeddings
        if embedGen:
            public_url, error = await upload_to_gcs(file_path, user_email)
            if public_url:
                os.remove(file_path)
                print(public_url)
                return jsonify({'success': 'File uploaded', 'url': public_url}), 200
            else:
                if error:
                    return jsonify({'error': f'GCS upload failed: {error}'}), 500

        return jsonify({'error': 'Embedding generation failed'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500
