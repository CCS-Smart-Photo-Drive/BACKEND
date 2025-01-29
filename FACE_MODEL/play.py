import os

from FACE_MODEL.import_libs import *
import numpy as np
import asyncio

# async def generate_event_embeddings(image_folder, event_name):
#     event_embeddings = {}
#     image_file_names = [
#         i for i in os.listdir(image_folder) if i.endswith(('.jpg', '.jpeg', '.png'))
#     ]
#
#     def image_processing(image_file):
#         try:
#             image_path = os.path.join(image_folder, image_file)
#             image = face_recognition.load_image_file(image_path)
#             event_image_embeddings = face_recognition.face_encodings(image)
#             if event_image_embeddings:
#                 event_embeddings[image_file] = [embedding.tolist() for embedding in event_image_embeddings]
#         except Exception as e:
#             print(f"Error processing {image_file}: {e}")
#
#     loop = asyncio.get_event_loop()
#     try:
#         with ThreadPoolExecutor() as executor:
#             await loop.run_in_executor(executor, lambda: list(map(image_processing, image_file_names)))
#     except Exception as e:
#         print(f"Error during threading: {e}")
#         return False
#
#     try:
#         with open('FACE_MODEL/event_photo_embedding.py', 'a') as g:
#             g.write(json.dumps({event_name: event_embeddings}) + '\n')
#     except Exception as e:
#         print(f"Error saving embeddings: {e}")
#         return False
#
#     return True

#Event ke saare photos ki embeddings create karega
def generate_event_embeddings(image_folder, event_name):
    event_embeddings = {}
    image_file_names = []
    for i in os.listdir(image_folder):
        if i.endswith('.jpg') or i.endswith('.jpeg') or i.endswith('.png'):
            image_file_names.append(i)
    print("yes2")
    def image_processing(image_file):
        print("yes1")
        image_path = os.path.join(image_folder, image_file)
        image = face_recognition.load_image_file(image_path)
        event_image_embeddings = face_recognition.face_encodings(image)
        if event_image_embeddings:
            event_embeddings[image_file] = [embedding.tolist() for embedding in event_image_embeddings]
    try:
        # with ThreadPoolExecutor() as executor:
        #     executor.map(image_processing, image_file_names)
        for i in range(len(image_file_names)):
            image_processing(image_file_names[i])
    except Exception as e:
        print(e)
        return False
    try:
        with open('FACE_MODEL/event_photo_embedding.py', 'a') as f:
            f.write(json.dumps({event_name: event_embeddings}) + '\n')
    except Exception as e:
        return False
    return True

#User ki DP ki embeddings create karega
def generate_user_embeddings(image_path, user_email, user_name):
    user_embeddings = {}
    if os.path.exists('user_embeddings.py'):
        with open('user_embeddings.py', 'r') as f:
            user_embeddings = json.loads(f.read())
    try:
        user_dp = face_recognition.load_image_file(image_path)
        user_dp_embeddings = face_recognition.face_encodings(user_dp)
        if user_dp_embeddings:
            user_embeddings[user_email] = {user_name: user_dp_embeddings[0].tolist()}
    except Exception as e:
        return False

    try:
        with open('FACE_MODEL/user_embeddings.py', 'w') as f:
            f.write(f"{json.dumps(user_embeddings)}\n")
    except Exception as e:
        return False
    return True

#User ko event ke photos me dhundega mast.
def finding_nemo(user_email, event_name):
    try:
        with open('FACE_MODEL/user_embeddings.py', 'r') as f:
            user_embeddings = json.loads(f.read())
        with open('FACE_MODEL/event_photo_embedding.py', 'r') as f:
            event_embeddings = json.loads(f.read())
    except Exception as e:
        return []

    try:
        user_embedding = user_embeddings.get(user_email)
        if not user_embedding:
            return []

        user_embedding = list(user_embedding.values())[0]
        # print(event_name)
        event_images_collection = event_embeddings.get(event_name, {})
        # print(event_images_collection)
        # further_event_images_collection  = list(event_images_collection.keys())
        # print(event_images_collection.keys())
    except Exception as e:
        return []

    def comparing_nemo_truly(image_file_name):
        event_embeddings_list = event_images_collection[image_file_name]
        # print("event_embeddings_list", event_embeddings_list)
        # print([user_embedding])
        for event_embedding in event_embeddings_list:
            match = face_recognition.compare_faces([user_embedding], np.array(event_embedding), tolerance = 0.6)
            if any(match):
                return image_file_name
        return None
    try:
        # with ThreadPoolExecutor() as executor:
        #     results = executor.map(comparing_nemo_truly, event_images_collection.keys())
        results = []
        print("len(event_images_collection.keys())", len(event_images_collection.keys()))
        for i in range(len(event_images_collection.keys())):
            x = comparing_nemo_truly(list(event_images_collection.keys())[i])
            results.append(x)
            # print("yes")
    except Exception:
        return []
    # print(results)
    return results
