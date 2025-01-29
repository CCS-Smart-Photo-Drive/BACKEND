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

#User Registrations
@app.route('/register_user', methods = ['POST'])
async def register_user():
    user_name = request.form['user_name']
    user_email = request.form['user_email']
    password = request.form['password']
    if user_name == '' or user_email == '' or password == '':
        return jsonify({'error': 'All fields are required'}), 400

    user = {
        'user_name': user_name,
        'email': user_email,
        'password': bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    }
    try:
        if user_collection.find_one({'email': user_email}):
            return jsonify({'error': 'Username already exists'}), 400
        user_collection.insert_one(user)
    except Exception as e:
        return jsonify({'error': str(e)}), 400


    return jsonify({'message': 'User successfully registered'}), 201

@app.route('/login_user', methods = ['POST'])
async def login_user():
    user_email = request.form['user_email']
    password = request.form['password']
    if user_email == '' or password == '':
        return jsonify({'error': 'All fields are required'}), 400
    user_email_on_db = user_collection.find_one({'email': user_email})

    if user_email_on_db and bcrypt.checkpw(password.encode('utf-8'), user_email_on_db['password'].encode('utf-8')):
        return jsonify({'message': 'User successfully logged in'}), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 400

@app.route("/change_password_user", methods=['POST'])
def password_badlo():
    user_email = request.form['user_email']
    old_password = request.form['old_password']
    new_password = request.form['new_password']
    if user_email == '' or old_password == '' or new_password == '':
        return jsonify({'error': 'All fields are required'}), 400
    user = user_collection.find_one({'email': user_email})
    if user and bcrypt.checkpw(old_password.encode('utf-8'), user['password'].encode('utf-8')):
        user_collection.update_one({'email': user_email}, {'$set': {'password': bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')}})
        return jsonify({'message': 'Password successfully updated'}), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 400
