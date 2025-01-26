from FACE_MODEL.import_libs import *

#Event ke saare photos ki embeddings create karega
def generate_event_embeddings(image_folder, event_name):
    event_embeddings = {}
    image_file_names = []
    for i in os.listdir(image_folder):
        if i.endswith('.jpg'):
            image_file_names.append(i)

    def image_processing(image_file):
        image_path = os.path.join(image_folder, image_file)
        image = face_recognition.load_image_file(image_path)
        event_image_embeddings = face_recognition.face_encodings(image)
        if event_image_embeddings:
            event_embeddings[image_file] = [embedding.tolist() for embedding in event_image_embeddings]
    try:
        with ThreadPoolExecutor() as executor:
            executor.map(image_processing, image_file_names)
    except Exception as e:
        return False
    try:
        with open('event_photo_embedding.py', 'a') as f:
            f.write(f"{event_name} = {json.dumps(event_embeddings)}\n")
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
        with open('user_embeddings.py', 'w') as f:
            f.write(f" {user_email} = {json.dumps(user_embeddings)}\n")
    except Exception as e:
        return False
    return True

#User ko event ke photos me dhundega mast.
def finding_nemo(user_email, event_name):
    try:
        with open('user_embeddings.py', 'r') as f:
            user_embeddings = json.loads(f.read())
        with open('event_photo_embedding.py', 'r') as f:
            event_embeddings = json.loads(f.read())
    except Exception as e:
        return []

    try:
        user_embedding = user_embeddings.get(user_email)
        if not user_embedding:
            return []

        user_embedding = list(user_embedding.values())[0]
        event_images_collection = event_embeddings.get(event_name, {})
    except Exception as e:
        return []

    def comparing_nemo_truly(image_file_name):
        event_embeddings_list = event_images_collection[image_file_name]
        for event_embedding in event_embeddings_list:
            match = face_recognition.compare_faces([user_embedding], event_embedding, tolerance = 0.6)
            if any(match):
                return image_file_name
        return None
    try:
        with ThreadPoolExecutor() as executor:
            results = executor.map(comparing_nemo_truly, event_images_collection.keys())
    except Exception as e:
        return []
    return [result for result in results if result]
