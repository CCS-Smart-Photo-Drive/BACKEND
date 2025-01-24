from flask import render_template, request, redirect, url_for, jsonify
from init_config import app, user_collection, event_manager_collection, events_collection
import cloudinary.uploader
import os
import zipfile
from werkzeug.utils import secure_filename


#LOGIN USERS
@app.route('/register_user', methods = ['POST'])
def register_user():
    user_name = request.form['user_name']
    email = request.form['email']
    password = request.form['password']
    if user_name == '' or email == '' or password == '':
        return jsonify({'error': 'All fields are required'}), 400

    user = {
        'user_name': user_name,
        'email': email,
        'password': password
    }
    try:
        if user_collection.find_one({'user_name': user_name}):
            return jsonify({'error': 'Username already exists'}), 400
        user_collection.insert_one(user)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


    return jsonify({'message': 'User successfully registered'}), 201
@app.route('/login_user', methods = ['POST'])
def login_user():
    user_name = request.form['user_name']
    password = request.form['password']
    if user_name == '' or password == '':
        return jsonify({'error': 'All fields are required'}), 400
    if user_collection.find_one({'user_name': user_name}) and user_collection.find_one({'password': password}):
        return jsonify({'message': 'User successfully logged in'}), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 400

#LOGIN EVENTS
@app.route('/register_event_manager', methods = ['POST'])
def register_event_mng():
    event_manager_name = request.form['event_manager_name']
    email = request.form['email']
    password = request.form['password']
    if event_manager_name == '' or email == '' or password == '':
        return jsonify({'error': 'All fields are required'}), 400
    event_manager = {
        'event_manager_name': event_manager_name,
        'email': email,
        'password': password
    }
    try:

        if event_manager_collection.find_one({'event_manager_name': event_manager_name}):
            return jsonify({'error': 'Username already exists'}), 400
        event_manager_collection.insert_one(event_manager)
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    return jsonify({'message': 'User successfully registered'}), 201


@app.route('/login_event_manager', methods = ['POST'])
def login_event_mng():
    event_manager_name = request.form['event_manager_name']
    password = request.form['password']
    if event_manager_name == '' or password == '':
        return jsonify({'error': 'All fields are required'}), 400
    if event_manager_collection.find_one({'event_manager_name': event_manager_name}) and event_manager_collection.find_one({'password': password}):
        return jsonify({'message': 'User successfully logged in'}), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 400

#EVENT MANAGER DASHBOARD
@app.route('/add_event', methods = ['POST'])
def add_event():
    event_manager_name = request.form['event_manager_name']
    event_name = request.form['event_name']
    description = request.form['description']
    organized_by = request.form['organized_by']
    date = request.form['date']

    if event_name == '' or description == '' or organized_by == '' or date == '':
        return jsonify({'error': 'All fields are required'}), 400

    event = {
        'event_manager_name': event_manager_name,
        'event_name': event_name,
        'description': description,
        'organized_by': organized_by,
        'date': date
    }
    try:
        if events_collection.find_one({'event_manager_name': event_manager_name}) and events_collection.find_one({'event_name': event_name}):
            return jsonify({'error': 'Event Already exists'}), 400
        events_collection.insert_one(event)
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    return jsonify({'message': 'User successfully registered'}), 201
@app.route('/my_events', methods = ['POST'])
def my_events():
    event_manager = request.form['event_manager_name']
    if event_manager == '':
        return jsonify({'error': 'All fields are required'}), 400
    events = list(events_collection.find({'event_manager_name': event_manager}))
    for event in events:
        event['_id'] = str([event['_id']])
    return jsonify({'events': events}), 200

@app.route('/all_events')
def all_events():
    pass

@app.route('/upload', methods = ['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No file selected for uploading'}), 400

    if file and file.filename.endswith('.zip'):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        try:
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(app.config['UPLOAD_FOLDER'])
        except (zipfile.BadZipFile, OSError) as e:
            return jsonify({'error': 'Error extracting the zip file'}), 500

        return jsonify({'message': 'File successfully uploaded and extracted'}), 201
    else:
        return jsonify({'error': 'Allowed file type is .zip'}), 400


#ABOUT US
@app.route('/about_us')
def about_us():
    pass