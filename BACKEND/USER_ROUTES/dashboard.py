import os
import zipfile
import shutil
from flask import  request, jsonify, send_file
from werkzeug.utils import secure_filename
import bcrypt
from BACKEND.init_config import user_collection, app, events_collection
from FACE_MODEL.play import generate_user_embeddings, finding_nemo
import cloudinary
import cloudinary.uploader
import requests
import asyncio

@app.route('/my_dashboard', methods=['POST'])
async def user_my_dashboard():
    user_name = request.form['user_name']
    user_email = request.form['user_email']
    if user_name == '':
        return jsonify({'error': 'All fields are required'}), 400
    if 'user_file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    user_dp = request.files['user_file']
    if user_dp.filename == '':
        return jsonify({'error': 'No file selected for uploading'}), 400

    try:
        filename = secure_filename(user_dp.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        user_dp.save(file_path)
        print("yes1")
        if generate_user_embeddings(file_path, user_email,  user_name):
            await asyncio.to_thread(cloudinary.uploader.upload, file_path, folder = "MY_USERS", public_id= user_name)
        print("yes2")
        # await asyncio.gather(task)



        os.remove(file_path)

        return jsonify({'message': 'User dashboard updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500