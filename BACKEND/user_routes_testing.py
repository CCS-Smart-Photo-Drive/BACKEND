# import os
# import zipfile
# import shutil
# from flask import  request, jsonify, send_file
# from werkzeug.utils import secure_filename
# import bcrypt
# from BACKEND.init_config import user_collection, app, events_collection
# from FACE_MODEL.play import generate_user_embeddings, finding_nemo
# import cloudinary
# import cloudinary.uploader
# import requests
# import asyncio
#
# #User Registrations
# @app.route('/register_user', methods = ['POST'])
# async def register_user():
#     user_name = request.form['user_name']
#     user_email = request.form['user_email']
#     password = request.form['password']
#     if user_name == '' or user_email == '' or password == '':
#         return jsonify({'error': 'All fields are required'}), 400
#
#     user = {
#         'user_name': user_name,
#         'email': user_email,
#         'password': bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
#     }
#     try:
#         if user_collection.find_one({'email': user_email}):
#             return jsonify({'error': 'Username already exists'}), 400
#         user_collection.insert_one(user)
#     except Exception as e:
#         return jsonify({'error': str(e)}), 400
#
#
#     return jsonify({'message': 'User successfully registered'}), 201
#
# #User Login
# @app.route('/login_user', methods = ['POST'])
# async def login_user():
#     user_email = request.form['user_email']
#     password = request.form['password']
#     if user_email == '' or password == '':
#         return jsonify({'error': 'All fields are required'}), 400
#     user_email_on_db = user_collection.find_one({'email': user_email})
#
#     if user_email_on_db and bcrypt.checkpw(password.encode('utf-8'), user_email_on_db['password'].encode('utf-8')):
#         return jsonify({'message': 'User successfully logged in'}), 200
#     else:
#         return jsonify({'error': 'Invalid credentials'}), 400
#
# @app.route("/change_password_user", methods=['POST'])
# def password_badlo():
#     user_email = request.form['user_email']
#     old_password = request.form['old_password']
#     new_password = request.form['new_password']
#     if user_email == '' or old_password == '' or new_password == '':
#         return jsonify({'error': 'All fields are required'}), 400
#     user = user_collection.find_one({'email': user_email})
#     if user and bcrypt.checkpw(old_password.encode('utf-8'), user['password'].encode('utf-8')):
#         user_collection.update_one({'email': user_email}, {'$set': {'password': bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')}})
#         return jsonify({'message': 'Password successfully updated'}), 200
#     else:
#         return jsonify({'error': 'Invalid credentials'}), 400
# #User Dashboard
# @app.route('/my_dashboard', methods=['POST'])
# async def user_my_dashboard():
#     user_name = request.form['user_name']
#     user_email = request.form['user_email']
#     if user_name == '':
#         return jsonify({'error': 'All fields are required'}), 400
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
#         user_dp.save(file_path)
#         if generate_user_embeddings(file_path, user_email,  user_name):
#             await asyncio.to_thread(cloudinary.uploader.upload, file_path, folder = "MY_USERS", public_id= user_name)
#
#         os.remove(file_path)
#
#         return jsonify({'message': 'User dashboard updated successfully'}), 200
#     except Exception as e:
#         return jsonify({'error': str(e)}), 500
#
# #Route for getting the photos.
#
#
# @app.route('/get_photos/<event_name>', methods=['GET', 'POST']) #EVENT ID DENI HAI
# async def getting_nemo(event_name):
#     if request.method == 'POST':
#         user_email = request.form['user_email']
#         try:
#             print("ok1")
#             image_names = await finding_nemo(user_email, event_name)
#             print(image_names)
#             if not image_names:
#                 return jsonify({'error': 'No images found'}), 404
#
#             zip_filename = f"{event_name}_photos.zip"
#             zip_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)
#             with zipfile.ZipFile(zip_path, 'w') as zipf:
#                 for image_name in image_names:
#                     image_url = cloudinary.CloudinaryImage(f"{event_name}/{image_name}.jpg").build_url()
#                     print("image_url", image_url)
#                     response = requests.get(image_url, stream=True)
#                     print("response", response)
#                     if response.status_code == 200:
#                         with open(image_name, 'wb') as img_file:
#                             shutil.copyfileobj(response.raw, img_file)
#                         zipf.write(image_name)
#                         os.remove(image_name)
#
#             return jsonify({'download_link': f"/get_photos/{event_name}?download={zip_filename}"}), 200
#         except Exception as e:
#             return jsonify({'error': str(e)}), 500
#     elif request.method == 'GET':
#         zip_filename = request.args.get('download')
#         if zip_filename:
#             file_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)
#             if os.path.exists(file_path):
#                 response = send_file(file_path, as_attachment=True)
#                 os.remove(file_path)
#                 return response
#             else:
#                 return jsonify({'error': 'File not found'}), 404
#         else:
#             return jsonify({'error': 'No file specified for download'}), 400
#
# @app.route('/all_events')
# async def all_events():
#     events = list(events_collection.find())
#     for event in events:
#         event['_id'] = str(event['_id'])
#     return jsonify({'events': events}), 200