import os
import zipfile
import shutil
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


async def upload_to_gcs(local_file_path, user_email):
    try:
        client = storage.Client()
        bucket_name = "ccs-host.appspot.com"
        bucket = client.bucket(bucket_name)

        filename = os.path.basename(local_file_path)
        blob_name = f"MY_USERS/{user_email}/{filename}"
        blob = bucket.blob(blob_name)

        # Asynchronous upload
        await asyncio.to_thread(blob.upload_from_filename, local_file_path)

        return True

    except Exception as e:
        return jsonify({'error': 'Embedding generation failed'}), 500

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
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        user_dp.save(file_path)

        if generate_user_embeddings(file_path, user_email, user_name):
            await upload_to_gcs(file_path, user_email)
            os.remove(file_path)
            return jsonify({'success': 'File uploaded and local copy deleted'}), 200

        return jsonify({'error': 'Embedding generation failed'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500