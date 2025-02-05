from flask import request, jsonify, g
from BACKEND.init_config import app
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from ..USER_ROUTES.authetication import auth_user
from ..EVENT_MANAGER_ROUTES.Authentication import auth_admin
import jwt
from dotenv import load_dotenv
import logging
import json
import os

load_dotenv()

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
        payload = jwt.decode(sso_token, jwt_secret, algorithms=['HS256'], leeway=10)
        decrypted_data = decrypt(payload['ex'], jwt_secret)
        return decrypted_data
    except jwt.ExpiredSignatureError as e:
        print(e)
        logger.warning(f"SSO token has expired.")
    except jwt.InvalidTokenError as e:
        print(e)
        logger.warning(f"SSO token is invalid.")
    return None

@app.route('/sso_auth', methods=['POST'])
def auth():
    sso_token = request.headers['Authorization'].split(" ")[1]
    if not sso_token:
        return jsonify({'error': 'Unauthorized'}), 401

    user_info = get_user_info_from_sso_token(sso_token)
    if not user_info:
        return jsonify({'error': 'Unauthorized'}), 401

    roles = []
    for role in user_info['roles']:
        roles.append(role['role'])

    if ('admin' or 'core' or 'exbo') in roles:
        data = auth_admin({
            'event_manager_name': user_info['name'],
            'email': user_info['email'],
        })
        data[0]['user']['is_admin'] = True
        return jsonify(data[0]), data[1]

    data = auth_user({
        'user_name': user_info['name'],
        'email': user_info['email'],
    })
    print(data)
    data[0]['user']['is_admin'] = False
    return jsonify(data[0]), data[1]