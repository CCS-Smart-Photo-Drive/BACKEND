from flask import Flask
from flask_pymongo import PyMongo

app = Flask(__name__)

#MONGO ka Kuch Kuch:

app.config["MONGO_URI"] = "mongodb+srv://jsrihari:hhaarrii@backend.rr3us.mongodb.net/"
mongo = PyMongo(app)

# Secret key for session management
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'upload_folder'  # Ensure this directory exists
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit uploads to 16 MB


# Import routes

import routes

if __name__ == '__main__':
    app.run(debug=True)

