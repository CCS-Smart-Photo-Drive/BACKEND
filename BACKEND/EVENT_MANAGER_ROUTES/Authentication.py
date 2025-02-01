import os
from flask import request, jsonify
from BACKEND.init_config import user_collection, app, tokens_collection, events_collection, event_manager_collection
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from jwt import decode, ExpiredSignatureError, InvalidTokenError
from secrets import token_urlsafe
import logging
import json
import bcrypt

logger = logging.getLogger(__name__)

def decrypt(encrypted_data, key):
    if len(key) < 32:
        raise ValueError('Key must be at least 32 characters long for AES-256 encryption.')

    iv = bytes.fromhex(encrypted_data[:32])
    encrypted_data = bytes.fromhex(encrypted_data[32:])
    encryption_key = key[:32].encode('utf-8')

    cipher = Cipher(algorithms.AES(encryption_key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()

    try:
        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
        clean_data = unpadder.update(decrypted_data) + unpadder.finalize()
        decrypted_json = json.loads(clean_data.decode('utf-8'))
        logger.debug("Data decrypted and parsed successfully.")
    except json.JSONDecodeError as e:
        logger.error("Failed to decode JSON during decryption.")
        raise
    except Exception as e:
        logger.exception("Unexpected error during decryption.")
        raise

    return decrypted_json

def get_user_info_from_sso_token(sso_token):
    jwt_secret = os.getenv('JWT_SECRET')
    try:
        payload = decode(sso_token, jwt_secret, algorithms=['HS256'], leeway=10)
        decrypted_data = decrypt(payload['ex'], jwt_secret)
        return decrypted_data
    except ExpiredSignatureError as e:
        logger.warning(f"SSO token has expired., {str(e)}")
    except InvalidTokenError as e:
        logger.warning(f"SSO token is invalid., {str(e)}")
    return None

# Event_manager Register.
@app.route('/sso_auth_admin', methods=['POST'])
async def admin_auth():
    sso_token = request.headers['Authorization'].split(" ")[1]
    if not sso_token:
        return jsonify({'error': 'Unauthorized'}), 401

    user_info = get_user_info_from_sso_token(sso_token)
    if not user_info:
        return jsonify({'error': 'Unauthorized'}), 401

    user_email = user_info['email']
    user_name = user_info['name']
    user = {
        'event_manager_name': user_name,
        'email': user_email,
    }

    token = token_urlsafe(16)

    try:
        existing_user = event_manager_collection.find_one({'email': user_email})
        if existing_user:
            tokens_collection.insert_one({
                'token': token,
                'user_id': existing_user['_id']
            })
            return jsonify({'user': {
                'event_manager_name': existing_user['event_manager_name'],
                'email': existing_user['email'],
            }, 'token': token }), 200
        event_manager_collection.insert_one(user)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    tokens_collection.insert_one({
        'token': token,
        'user_id': existing_user['_id']
    })
    return jsonify({'user': user, 'token': token}), 201

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
