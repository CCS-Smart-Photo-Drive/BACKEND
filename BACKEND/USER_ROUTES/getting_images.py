import os
import zipfile
import shutil
from flask import  request, jsonify, send_file, g
from BACKEND.init_config import  app
from FACE_MODEL.play import finding_nemo
import requests

from google.cloud import storage
import asyncio

# Initialize Google Cloud Storage Client with Service Account
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Directory of this script
SERVICE_ACCOUNT_PATH = os.path.join(BASE_DIR, "..", "config", "serviceAccount.json")

# Initialize the client
client = storage.Client.from_service_account_json(SERVICE_ACCOUNT_PATH)
bucket_name = "ccs-host.appspot.com"
bucket = client.bucket(bucket_name)

async def get_gcs_image_urls(event_name, image_names):
    try:
        image_urls = []

        for image_name in image_names:
            blob_name = f"upload_folder/{event_name}/{image_name}"  # Full GCS path
            blob = bucket.blob(blob_name)

            if blob.exists():
                image_urls.append(f"https://storage.googleapis.com/{bucket_name}/{blob_name}")
            else:
                continue  # Skip if the image doesn't exist

        return image_urls

    except Exception as e:
        print(f"Error fetching images from GCS: {e}")
        return None

@app.route('/get_photos/<event_name>', methods=['GET', 'POST'])
async def getting_nemo(event_name):
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    if request.method == 'GET':
        zip_filename = request.args.get('download')
        if not zip_filename:
            return jsonify({'error': 'No file specified for download'}), 400
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)

        try:
            return send_file(file_path, download_name=zip_filename, mimetype="application/zip", as_attachment=True)
        except Exception as e:
            print(e)
            return jsonify({'error': 'File not found'}), 404

    user_email = g.user['email']
    try:
        image_names = await finding_nemo(user_email, event_name)
        if not image_names:
            return jsonify({'error': 'No images found'}), 404

        image_urls = await get_gcs_image_urls(event_name, image_names)
        if not image_urls:
            return jsonify({'error': 'Images not found in GCS'}), 404


        zip_filename = f"{event_name}_photos.zip"
        zip_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)

        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for image_name, image_url in zip(image_names, image_urls):
                print("Downloading:", image_url)
                response = requests.get(image_url, stream=True)

                if response.status_code != 200:
                    continue  # Skip if the image can't be fetched

                local_image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_name)
                with open(local_image_path, 'wb') as img_file:
                    shutil.copyfileobj(response.raw, img_file)

                zipf.write(local_image_path, arcname=image_name)
                os.remove(local_image_path)  # Clean up the local copy

        return jsonify({
            'download': zip_filename,
            'image_urls': jsonify(image_urls)  # Return public URLs of images
        }), 200

    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500
# @app.route('/get_photos/<event_name>', methods=['GET', 'POST']) #EVENT ID DENI HAI
# async def getting_nemo(event_name):
#     os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
#     if request.method == 'GET':
#         zip_filename = request.args.get('download')
#         if not zip_filename:
#             return jsonify({'error': 'No file specified for download'}), 400
#         file_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)
#         print(file_path)
#
#         try:
#             file = open(os.path.join(app.config['UPLOAD_FOLDER'], zip_filename), "rb")
#         except Exception as e:
#             print(e)
#             return jsonify({'error': 'File not found'}), 404
#
#         response = send_file(file, download_name=zip_filename, mimetype="application/zip", as_attachment=True)
#         return response
#
#     user_email = g.user['email']
#     try:
#         image_names = await finding_nemo(user_email, event_name)
#         print(image_names)
#         if not image_names:
#              return jsonify({'error': 'No images found'}), 404
#
#         zip_filename = f"{event_name}_photos.zip"
#         zip_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)
#         with zipfile.ZipFile(zip_path, 'w') as zipf:
#             for image_name in image_names:
#                 image_url = cloudinary.CloudinaryImage(f"{event_name}/{image_name}.jpg").build_url()
#                 print("image_url", image_url)
#                 response = requests.get(image_url, stream=True)
#                 print("response", response)
#                 if response.status_code != 200:
#                     continue
#                 with open(image_name, 'wb') as img_file:
#                     shutil.copyfileobj(response.raw, img_file)
#                 zipf.write(image_name)
#                 os.remove(image_name)
#
#
#         return jsonify({'download': zip_filename}), 200
#     except Exception as e:
#         print(e)
#         return jsonify({'error': str(e)}), 500
