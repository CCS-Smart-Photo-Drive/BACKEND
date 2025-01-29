from flask import Flask
from flask_pymongo import PyMongo
from flask_cors import CORS
app = Flask(__name__)
CORS(app, resources=["*"], origins='*')

#MONGO ka Kuch Kuch:

DEV = True
app.config["MONGO_URI"] = "ADD URS HERE"
mongo = PyMongo(app)
user_collection = mongo.db.users
event_manager_collection = mongo.db.events_manager
events_collection = mongo.db.events
images_collection = mongo.db.images

app.config['SECRET_KEY'] = "ADD URS HERE"
app.config['UPLOAD_FOLDER'] = 'BACKEND\\upload_folder'
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  #Upload Limit 20 MB
