from flask import Flask
from flask_pymongo import PyMongo
from flask_cors import CORS
app = Flask(__name__)
CORS(app, resources=["*"], origins='*')
# CORS(app, resources={r"/*": {"origins": "*"}})

#MONGO ka Kuch Kuch:

