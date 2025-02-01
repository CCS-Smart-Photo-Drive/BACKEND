from FACE_MODEL.import_libs import *
import numpy as np
import asyncio
import multiprocessing


def process_image(image_path):
    try:
        image = cv2.imread(image_path)
        img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        event_image_embeddings = face_recognition.face_encodings(img)

        if event_image_embeddings:
            return os.path.basename(image_path), [embedding.tolist() for embedding in event_image_embeddings]
    except Exception as e:
        print(f"Error processing {image_path}: {e}")

    return None


async def generate_event_embeddings(image_folder, event_name):
    image_file_names = [
        os.path.join(image_folder, f) for f in os.listdir(image_folder) if f.endswith(('.jpg', '.jpeg', '.png'))
    ]

    num_workers = min(multiprocessing.cpu_count(), len(image_file_names))

    with multiprocessing.Pool(num_workers) as pool:
        results = await asyncio.get_running_loop().run_in_executor(None,
                                                                   lambda: pool.map(process_image, image_file_names))

    event_embeddings = {img: emb for img, emb in results if emb is not None}

    try:
        with open('FACE_MODEL/event_photo_embedding.json', 'a') as g:
            json.dump({event_name: event_embeddings}, g)
            g.write('\n')
    except Exception as e:
        print(f"Error saving embeddings: {e}")
        return False

    return True

# #Event ke saare photos ki embeddings create karega
# def generate_event_embeddings(image_folder, event_name):
#     event_embeddings = {}
#     image_file_names = []
#     for i in os.listdir(image_folder):
#         if i.endswith('.jpg') or i.endswith('.jpeg') or i.endswith('.png'):
#             image_file_names.append(i)
#     print("yes2")
#     def image_processing(image_file):
#         print("yes1")
#         image_path = os.path.join(image_folder, image_file)
#         image = face_recognition.load_image_file(image_path)
#         event_image_embeddings = face_recognition.face_encodings(image)
#         if event_image_embeddings:
#             event_embeddings[image_file] = [embedding.tolist() for embedding in event_image_embeddings]
#     try:
#         # with ThreadPoolExecutor() as executor:
#         #     executor.map(image_processing, image_file_names)
#         for i in range(len(image_file_names)):
#             image_processing(image_file_names[i])
#     except Exception as e:
#         print(e)
#         return False
#     try:
#         with open('FACE_MODEL/event_photo_embedding.py', 'a') as f:
#             f.write(json.dumps({event_name: event_embeddings}) + '\n')
#     except Exception as e:
#         return False
#     return True

#User ki DP ki embeddings create karega
# def generate_user_embeddings(image_path, user_email, user_name):
#     user_embeddings = {}
#     if os.path.exists('user_embeddings.py'):
#         with open('user_embeddings.py', 'r') as f:
#             user_embeddings = json.loads(f.read())
#     # print("ok1")
#     try:
#         user_dp = face_recognition.load_image_file(image_path)
#         # print("ok2")
#         user_dp_embeddings = face_recognition.face_encodings(user_dp)
#         # print("ok3")
#         if user_dp_embeddings:
#             user_embeddings[user_email] = {user_name: user_dp_embeddings[0].tolist()}
#             # print("ok4")
#         # print("ok5")
#     except Exception as e:
#         return False
#
#     try:
#         with open('FACE_MODEL/user_embeddings.py', 'w') as f:
#             f.write(f"{json.dumps(user_embeddings)}\n")
#     except Exception as e:
#         return False
#     return True

#User ki DP ki embeddings create karega
def process_user_image(image_path):
    try:
        user_dp = cv2.imread(image_path)
        user_dp = cv2.cvtColor(user_dp, cv2.COLOR_BGR2RGB)
        user_dp_embeddings = face_recognition.face_encodings(user_dp)

        if user_dp_embeddings:
            return user_dp_embeddings[0].tolist()
    except Exception as e:
        print(f"Error processing user image {image_path}: {e}")
    return None


def generate_user_embeddings(image_path, user_email, user_name):

    user_embeddings = {}

    if os.path.exists('FACE_MODEL/user_embeddings.json'):
        with open('FACE_MODEL/user_embeddings.json', 'r') as f:
            try:
                user_embeddings = json.load(f)
            except json.JSONDecodeError:
                user_embeddings = {}

    with multiprocessing.Pool(1) as pool:
        result = pool.apply(process_user_image, (image_path,))

    if result:
        user_embeddings[user_email] = {user_name: result}
    else:
        return False

    try:
        with open('FACE_MODEL/user_embeddings.json', 'w') as f:
            json.dump(user_embeddings, f, indent=4)
    except Exception as e:
        print(f"Error saving user embeddings: {e}")
        return False

    return True


#User ko event ke photos me dhundega mast.
def compare_nemo(user_embedding, image_file, event_embedding):
    try:
        user_embedding_np = np.array(user_embedding)
        event_embedding_np = np.array(event_embedding)
        match = face_recognition.compare_faces([user_embedding_np], event_embedding_np)
        if any(match):
            return image_file
    except Exception as e:
        print(f"Error in comparison: {e}")
    return None

async def finding_nemo(user_email, event_name):
    try:
        with open('FACE_MODEL/user_embeddings.json', 'r') as f:
            user_embeddings = json.load(f)
        with open('FACE_MODEL/event_photo_embedding.json', 'r') as f:
            event_embeddings = json.load(f)
    except Exception as e:
        print(f"Error loading JSON files: {e}")
        return []

    user_embedding = user_embeddings.get(user_email)
    if not user_embedding:
        print('user embeddings empty')
        return []

    user_embedding = list(user_embedding.values())[0]

    event_images_collection = event_embeddings.get(event_name, {})
    if not event_images_collection:
        print('event images collection empty')
        return []

    event_embeddings_list = [(img, emb) for img, emb in event_images_collection.items()]

    num_workers = min(multiprocessing.cpu_count(), len(event_embeddings_list))  # Optimize worker count

    with multiprocessing.Pool(num_workers) as pool:
        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(
            None,
            lambda: list(filter(None, pool.starmap(compare_nemo, [(user_embedding, img, emb) for img, emb in event_embeddings_list])))
        )

    return results