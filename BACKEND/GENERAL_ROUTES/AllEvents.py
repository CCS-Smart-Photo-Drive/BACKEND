import os
import zipfile
import shutil
from flask import Flask, request, jsonify
import bcrypt
import BACKEND.config
from werkzeug.utils import secure_filename
import cloudinary
import cloudinary.uploader
from FACE_MODEL import play
from BACKEND.init_config import events_collection, app, event_manager_collection
import asyncio

@app.route('/all_events')
async def all_events():
    events = list(events_collection.find())
    for event in events:
        event['_id'] = str(event['_id'])
        event['location'] = 'Thapar'
    return jsonify({'events': events}), 200

@app.route('/test', methods = ['GET'])
def home():
    #comment for testing
    return jsonify({'message': 'server is up and running'}), 200