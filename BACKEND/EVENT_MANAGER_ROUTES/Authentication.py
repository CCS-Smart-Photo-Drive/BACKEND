import os
import zipfile
import shutil
from flask import Flask, request, jsonify
import bcrypt
import BACKEND.config
from werkzeug.utils import secure_filename
import cloudinary
import cloudinary.uploader
from FACE_MODEL import play
from BACKEND.init_config import events_collection, app, event_manager_collection
import asyncio

# Event_manager Register.
@app.route('/register_event_manager', methods=['POST'])
async def register_event_mng():
    event_manager_name = request.form['event_manager_name']
    email = request.form['email']
    password = request.form['password']
    if event_manager_name == '' or email == '' or password == '':
        return jsonify({'error': 'All fields are required'}), 400
    event_manager = {
        'event_manager_name': event_manager_name,
        'email': email,
        'password': bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    }
    try:
        if event_manager_collection.find_one({'event_manager_name': event_manager_name}):
            return jsonify({'error': 'Username already exists'}), 400
        event_manager_collection.insert_one(event_manager)
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    return jsonify({'message': 'User successfully registered', 'name': "hari"}), 201

# Event_manager Login
@app.route('/login_event_manager', methods=['POST'])
async def login_event_mng():
    event_manager_name = request.form['event_manager_name']
    password = request.form['password']
    if event_manager_name == '' or password == '':
        return jsonify({'error': 'All fields are required'}), 400
    event_manager = event_manager_collection.find_one({'event_manager_name': event_manager_name})
    if event_manager and bcrypt.checkpw(password.encode('utf-8'), event_manager['password'].encode('utf-8')):
        return jsonify({'message': 'User successfully logged in', 'name': "hari"}), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 400
