import os
import face_recognition
import cv2
from concurrent.futures import ThreadPoolExecutor
import json

def generate_event_embeddings(image_folder, event_name, event_manager_name):
    event_embeddings = {}
    image_files = []
    for f in os.listdir(image_folder):
        if f.endswith('.jpg'):
            image_files.append(f)

    def process_image(image_file):
        image_path = os.path.join(image_folder, image_file)
        image = face_recognition.load_image_file(image_path)
        embeddings = face_recognition.face_encodings(image)
        if embeddings:
            event_embeddings[image_file] = [embedding.tolist() for embedding in embeddings]

    with ThreadPoolExecutor() as executor:
        executor.map(process_image, image_files)

    with open('event_photo_embedding.py', 'a') as f:
        f.write(f"{event_name} = {json.dumps(event_embeddings)}\n")

def generate_user_embeddings(image_path, user_email, user_name):
    user_embeddings = {}
    if os.path.exists('user_embeddings.py'):
        with open('user_embeddings.py', 'r') as f:
            user_embeddings = json.loads(f.read())

    image = face_recognition.load_image_file(image_path)
    embeddings = face_recognition.face_encodings(image)
    if embeddings:
        user_embeddings[user_email] = {user_name: embeddings[0].tolist()}

    with open('user_embeddings.py', 'w') as f:
        f.write(f" {user_email} = {json.dumps(user_embeddings)}\n")

def find_user_in_event(user_email, event_name):
    with open('user_embeddings.py', 'r') as f:
        user_embeddings = json.loads(f.read())
    with open('event_photo_embedding.py', 'r') as f:
        event_embeddings = json.loads(f.read())

    user_embedding = user_embeddings.get(user_email)
    if not user_embedding:
        return []

    user_embedding = list(user_embedding.values())[0]
    event_images = event_embeddings.get(event_name, {})

    def compare_embeddings(image_file):
        event_embeddings_list = event_images[image_file]
        for event_embedding in event_embeddings_list:
            match = face_recognition.compare_faces([user_embedding], event_embedding, tolerance = 0.6)
            if any(match):
                return image_file
        return None

    with ThreadPoolExecutor() as executor:
        results = executor.map(compare_embeddings, event_images.keys())

    return [result for result in results if result]

