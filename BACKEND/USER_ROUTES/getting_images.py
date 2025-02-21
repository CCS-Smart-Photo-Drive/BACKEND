import os
import zipfile
import shutil
from flask import  request, jsonify, send_file, g
from BACKEND.init_config import  app
from FACE_MODEL.play import finding_nemo
import cloudinary
import cloudinary.uploader
import requests

@app.route('/get_photos/<event_name>', methods=['GET', 'POST']) #EVENT ID DENI HAI
async def getting_nemo(event_name):
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    if request.method == 'GET':
        zip_filename = request.args.get('download')
        if not zip_filename:
            return jsonify({'error': 'No file specified for download'}), 400
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)
        print(file_path)

        try:
            file = open(os.path.join(app.config['UPLOAD_FOLDER'], zip_filename), "rb")
        except Exception as e:
            print(e)
            return jsonify({'error': 'File not found'}), 404

        response = send_file(file, download_name=zip_filename, mimetype="application/zip", as_attachment=True)
        return response

    user_email = g.user['email']
    try:
        image_names = await finding_nemo(user_email, event_name)
        print(image_names)
        if not image_names:
             return jsonify({'error': 'No images found'}), 404

        zip_filename = f"{event_name}_photos.zip"
        zip_path = os.path.join(app.config['UPLOAD_FOLDER'], zip_filename)
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for image_name in image_names:
                image_url = cloudinary.CloudinaryImage(f"{event_name}/{image_name}.jpg").build_url()
                print("image_url", image_url)
                response = requests.get(image_url, stream=True)
                print("response", response)
                if response.status_code != 200:
                    continue
                with open(image_name, 'wb') as img_file:
                    shutil.copyfileobj(response.raw, img_file)
                zipf.write(image_name)
                os.remove(image_name)


        return jsonify({'download': zip_filename}), 200
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)}), 500
