import os

from bson import ObjectId
from flask import Flask, request, jsonify, g
from flask_pymongo import PyMongo
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, resources=["*"], origins="https://api-smartdrive.ccstiet.com", supports_credentials=True)
# CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

def path_request_auth(path):
    return path not in [
        '/sso_auth', '/sso_auth_user', '/sso_auth_admin', '/all_events', '/about_us',
        '/register_event_manager', '/register_user',
        '/login_event_manager', '/login_user',
        '/test',
    ]

def path_request_admin(path):
    return path in ['/my_events', '/add_new_event']

@app.before_request
def auth():
    if request.method == "OPTIONS":
        return '', 200

    if not path_request_auth(request.path):
        return

    auth_header = request.headers.get("Authorization")
    if not auth_header or "Bearer " not in auth_header:
        return jsonify({"error": "Unauthorized"}), 401

    token = auth_header.split(" ")[1]  # Extract token

    data = tokens_collection.find_one({'token': token})
    if not data:
        return jsonify({"error": "Unauthorized"}), 401

    user = {
        'user_name': None,
        'email': None,
        'is_admin': False,
    }

    user_data = user_collection.find_one({'_id': ObjectId(data['user_id'])})
    if user_data:
        if path_request_admin(request.path):
            return jsonify({"error": "Unauthorized"}), 401
        user['user_name'] = user_data['user_name']
        user['email'] = user_data['email']
        user['is_admin'] = False
    else:
        event_manager_data = event_manager_collection.find_one({'_id': ObjectId(data['user_id'])})
        if not event_manager_data:
            return jsonify({"error": "Unauthorized"}), 401
        user['user_name'] = event_manager_data['event_manager_name']
        user['email'] = event_manager_data['email']
        user['is_admin'] = True

    g.user = user
    g.token = token

@app.after_request
def add_cors_headers(response):
    """ Ensure CORS headers are added to every response """
    response.headers["Access-Control-Allow-Origin"] = os.getenv("ALLOWED_ORIGINS")
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Event-Name, X-Description, X-Organized-By, X-Date, X-Event-Manager-Name, X-Event-Manager-Email"
    return response

app.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo = PyMongo(app)
user_collection = mongo.db.users
event_manager_collection = mongo.db.events_manager
events_collection = mongo.db.events
images_collection = mongo.db.images
tokens_collection = mongo.db.tokens

app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config['UPLOAD_FOLDER'] = os.path.join('BACKEND', 'upload_folder')
app.config['PARTIAL'] = 'upload_folder'
app.config['MAX_CONTENT_LENGTH'] = 200000 * 1024 * 1024  #Upload Limit 20 MB

