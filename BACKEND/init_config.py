from flask import Flask
from flask_pymongo import PyMongo
app = Flask(__name__)

#MONGO ka Kuch Kuch:

DEV = True
app.config["MONGO_URI"] = "mongodb://localhost:27017/Main" if DEV is True else "mongodb+srv://jsrihari:@backend.rr3us.mongodb.net/backend"
mongo = PyMongo(app)
user_collection = mongo.db.users
event_manager_collection = mongo.db.events_manager
events_collection = mongo.db.events
images_collection = mongo.db.images

app.config['SECRET_KEY'] = 'e22296e5ec72eaf368c57ca2cce57b37'
app.config['UPLOAD_FOLDER'] = 'upload_folder'
app.config['MAX_CONTENT_LENGTH'] = 20 * 1024 * 1024  #Upload Limit 20 MB
