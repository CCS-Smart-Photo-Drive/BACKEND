from flask import Flask
from flask_pymongo import PyMongo

app = Flask(__name__)

#MONGO ka Kuch Kuch:

DEV = True
app.config["MONGO_URI"] = "apna uri daalo"
mongo = PyMongo(app)
user_collection = mongo.db.users
event_manager_collection = mongo.db.events_manager
events_collection = mongo.db.events
images_collection = mongo.db.images

# Secret key for session management
app.config['SECRET_KEY'] = 'e22296e5ec72eaf368c57ca2cce57b37'
app.config['UPLOAD_FOLDER'] = 'upload_folder'  # Ensure this directory exists
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit uploads to 16 MB
