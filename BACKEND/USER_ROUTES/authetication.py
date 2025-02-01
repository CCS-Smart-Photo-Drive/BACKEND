import os

import cloudinary
import requests
from flask import  request, jsonify, g
from BACKEND.init_config import user_collection, app, tokens_collection
from secrets import token_urlsafe
import bcrypt
import base64

@app.route('/get_user_status', methods = ['GET'])
def user_status():
    return jsonify({
        'status': g.user['is_admin']
    })

def auth_user(user):
    token = token_urlsafe(16)

    try:
        existing_user = user_collection.find_one({'email': user['email']})
        if existing_user:
            tokens_collection.insert_one({
                'token': token,
                'user_id': existing_user['_id']
            })
            image_url = cloudinary.CloudinaryImage(f"MY_USERS/{user['email']}.jpg").build_url()
            response = requests.get(image_url, stream=True)

            image_base64 = base64.b64encode(response.content).decode("utf-8")
            return {'user': {
                'user_name': existing_user['user_name'],
                'email': existing_user['email'],
                'profile_picture': f"data:image/jpeg;base64,{image_base64}",
            }, 'token': token }, 200
        user_collection.insert_one(user)
    except Exception as e:
        return {'error': str(e)}, 400

    tokens_collection.insert_one({
        'token': token,
        'user_id': existing_user['_id']
    })
    return {'user': user, 'token': token}, 201


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
        new_user = user_collection.insert_one(user)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    token = token_urlsafe(16)

    tokens_collection.insert_one({
        'token': token,
        'user_id': new_user.inserted_id
    })

    return jsonify({'user': {
        'user_name': user_name,
        'email': user_email,
    }, 'token': token }), 201

@app.route('/login_user', methods = ['POST'])
async def login_user():
    user_email = request.form['user_email']
    password = request.form['password']
    if user_email == '' or password == '':
        return jsonify({'error': 'All fields are required'}), 400
    user_email_on_db = user_collection.find_one({'email': user_email})

    if not (user_email_on_db and bcrypt.checkpw(password.encode('utf-8'), user_email_on_db['password'].encode('utf-8'))):
        return jsonify({'error': 'Invalid credentials'}), 400

    token = token_urlsafe(16)

    tokens_collection.insert_one({
        'token': token,
        'user_id': user_email_on_db['_id']
    })

    image_url = cloudinary.CloudinaryImage(f"MY_USERS/{user_email}.jpg").build_url()
    response = requests.get(image_url, stream=True)

    image_base64 = base64.b64encode(response.content).decode("utf-8")

    return jsonify({'user': {
        'user_name': user_email_on_db['user_name'],
        'email': user_email_on_db['email'],
        'profile_picture': f"data:image/jpeg;base64,{image_base64}",
    }, 'token': token }), 200

@app.route('/logout', methods = ['POST'])
def logout():
    tokens_collection.delete_one({'token': g.token})
    return jsonify({'message': 'Logged out successfully'}), 200
