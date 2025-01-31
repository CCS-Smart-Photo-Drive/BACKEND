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
@app.route('/auth_admin', methods=['POST'])
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
        'user_name': user_name,
        'email': user_email,
        'is_admin': True,
    }

    token = token_urlsafe(16)

    try:
        existing_user = user_collection.find_one({'email': user_email})
        if existing_user:
            tokens_collection.insert_one({
                'token': token,
                'user_id': existing_user['_id']
            })
            return jsonify({'user': {
                'user_name': existing_user['user_name'],
                'email': existing_user['email'],
                'is_admin': existing_user['is_admin']
            }, 'token': token }), 200
        user_collection.insert_one(user)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    tokens_collection.insert_one({
        'token': token,
        'user_id': existing_user['_id']
    })
    return jsonify({'user': user, 'token': token}), 201