import os
from flask import request, jsonify
from BACKEND.init_config import user_collection, app, tokens_collection, events_collection, event_manager_collection
from secrets import token_urlsafe
import bcrypt


def auth_admin(user):
    token = token_urlsafe(16)

    try:
        existing_user = event_manager_collection.find_one({'email': user['email']})
        if existing_user:
            tokens_collection.insert_one({
                'token': token,
                'user_id': existing_user['_id']
            })
            return {'user': {
                'event_manager_name': existing_user['event_manager_name'],
                'email': existing_user['email'],
            }, 'token': token}, 200
        user = event_manager_collection.insert_one(user)
    except Exception as e:
        return {'error': str(e)}, 400

    tokens_collection.insert_one({
        'token': token,
        'user_id': user['_id']
    })
    return {'user': user, 'token': token}, 201

@app.route('/register_event_manager', methods = ['POST'])
async def register_event_manager():
    user_name = request.form['event_manager_name']
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
        if event_manager_collection.find_one({'email': user_email}):
            return jsonify({'error': 'Username already exists'}), 400
        new_user = event_manager_collection.insert_one(user)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    token = token_urlsafe(16)

    tokens_collection.insert_one({
        'token': token,
        'user_id': new_user['_id']
    })

    return jsonify({'user': {
        'user_name': user_name,
        'email': user_email,
    }, 'token': token }), 201

@app.route('/login_event_manager', methods = ['POST'])
async def login_event_manager():
    user_name = request.form['event_manager_name']
    password = request.form['password']
    if user_name == '' or password == '':
        print(1)
        return jsonify({'error': 'All fields are required'}), 400
    user_email_on_db = event_manager_collection.find_one({'event_manager_name': user_name})

    if not (user_email_on_db and bcrypt.checkpw(password.encode('utf-8'), user_email_on_db['password'].encode('utf-8'))):
        print(2)
        return jsonify({'error': 'Invalid credentials'}), 400


    token = token_urlsafe(16)

    tokens_collection.insert_one({
        'token': token,
        'user_id': user_email_on_db['_id']
    })

    return jsonify({'user': {
        'event_manager_name': user_email_on_db['event_manager_name'],
        'email': user_email_on_db['email'],
    }, 'token': token }), 200
