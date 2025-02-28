from FACE_MODEL.import_libs import *
import numpy as np
import asyncio
import multiprocessing
import torch
import os
import cv2
import json
import face_recognition

# Check if GPU is available
has_cuda = torch.cuda.is_available()
has_mps = hasattr(torch, 'mps') and torch.backends.mps.is_available()  # For Apple Silicon
device = torch.device("cuda" if has_cuda else "mps" if has_mps else "cpu")

print(f"Using device: {device}")

# Create a batch processor for GPU to process multiple images at once
def batch_process_images(image_paths, batch_size=4):
    """Process images in batches for GPU efficiency"""
    results = []
    
    for i in range(0, len(image_paths), batch_size):
        batch_paths = image_paths[i:i+batch_size]
        batch_images = []
        valid_indices = []
        
        for idx, path in enumerate(batch_paths):
            try:
                image = cv2.imread(path)
                if image is not None:
                    img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    batch_images.append(img)
                    valid_indices.append(idx)
            except Exception as e:
                print(f"Error reading {path}: {e}")
        
        if not batch_images:
            continue
            
        # If using GPU, convert to appropriate format
        if device.type != "cpu":
            # This is a placeholder - face_recognition doesn't directly support GPU
            # But we'd convert data to GPU format here if using a GPU-enabled face recognition library
            pass
            
        # Process the batch
        batch_embeddings = [face_recognition.face_encodings(img) for img in batch_images]
        
        # Store results
        for idx, embeddings in zip(valid_indices, batch_embeddings):
            path = batch_paths[idx]
            if embeddings:
                results.append((os.path.basename(path), [embedding.tolist() for embedding in embeddings]))
            else:
                results.append((path, None))
                
    return results

def process_image(image_path):
    """Process a single image - used for CPU processing"""
    try:
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Image could not be read")

        img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        event_image_embeddings = face_recognition.face_encodings(img)

        if event_image_embeddings:
            return os.path.basename(image_path), [embedding.tolist() for embedding in event_image_embeddings]

    except Exception as e:
        print(f"Error processing {image_path}: {e}")

    return (image_path, None)  # Ensure a tuple is always returned

async def generate_event_embeddings(image_folder, event_name):
    json_path = 'FACE_MODEL/event_photo_embedding.json'

    # Ensure the folder exists
    if not os.path.exists(image_folder):
        print(f"Error: Folder {image_folder} not found!")
        return False

    image_file_names = [
        os.path.join(image_folder, f) for f in os.listdir(image_folder) if f.endswith(('.jpg', '.jpeg', '.png'))
    ]

    if not image_file_names:
        print("No images found in the folder.")
        return False

    # Configure processing approach based on available hardware
    results = []
    if device.type != "cpu" and len(image_file_names) > 4:
        # Use GPU for batch processing if available and enough images
        print("Processing with GPU acceleration in batches")
        batch_size = 8 if has_cuda else 4  # Larger batches for NVIDIA GPUs
        results = await asyncio.get_running_loop().run_in_executor(
            None, lambda: batch_process_images(image_file_names, batch_size)
        )
    else:
        # Fall back to CPU processing with multiprocessing
        print("Processing with CPU multiprocessing")
        num_workers = min(multiprocessing.cpu_count(), len(image_file_names))
        num_workers = num_workers - 1 if num_workers > 1 else 1
        num_workers = max(2, num_workers)
        
        with multiprocessing.Pool(num_workers) as pool:
            results = await asyncio.get_running_loop().run_in_executor(
                None, lambda: pool.map(process_image, image_file_names)
            )

    filtered_results = {}
    for res in results:
        if res is not None:
            img, emb = res
            if emb is not None:  # Only add if embeddings were found
                filtered_results[img] = emb

    if not filtered_results:
        print("No valid embeddings generated.")
        return False

    # Load existing JSON safely
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as g:
                existing_data = json.load(g)
        except (json.JSONDecodeError, FileNotFoundError):
            existing_data = {}
    else:
        existing_data = {}

    # Merge new embeddings with existing ones
    existing_data[event_name] = filtered_results

    # Save the updated data safely
    try:
        with open(json_path, 'w', encoding='utf-8') as g:
            json.dump(existing_data, g, indent=4)
    except Exception as e:
        print(f"Error saving embeddings: {e}")
        return False

    return True

def process_user_image(image_path):
    """Process a single user profile image"""
    try:
        user_dp = cv2.imread(image_path)
        if user_dp is None:
            raise ValueError("User image could not be read")
            
        user_dp = cv2.cvtColor(user_dp, cv2.COLOR_BGR2RGB)
        
        # If using GPU and available, process on GPU
        if device.type != "cpu":
            # This is a placeholder - face_recognition doesn't directly support GPU
            # But we'd process on GPU here if using a GPU-enabled face recognition library
            pass
            
        face_locations = face_recognition.face_locations(user_dp)
        user_dp_embeddings = face_recognition.face_encodings(user_dp, face_locations)

        if user_dp_embeddings:
            return user_dp_embeddings[0].tolist()
    except Exception as e:
        print(f"Error processing user image {image_path}: {e}")
    return None


def generate_user_embeddings(image_path, user_email, user_name):
    """Generate embeddings for a user profile image"""
    user_embeddings = {}

    if os.path.exists('FACE_MODEL/user_embeddings.json'):
        with open('FACE_MODEL/user_embeddings.json', 'r') as f:
            try:
                user_embeddings = json.load(f)
            except json.JSONDecodeError:
                user_embeddings = {}

    # Process the image - single image so simple processing is fine
    result = process_user_image(image_path)

    if result:
        if user_email not in user_embeddings:
            user_embeddings[user_email] = {}
        user_embeddings[user_email][user_name] = result
    else:
        return False

    try:
        with open('FACE_MODEL/user_embeddings.json', 'w') as f:
            json.dump(user_embeddings, f, indent=4)
    except Exception as e:
        print(f"Error saving user embeddings: {e}")
        return False

    return True

def compare_nemo(user_embedding, image_file, event_embedding):
    """Compare a user embedding with an event embedding"""
    try:
        user_embedding_np = np.array(user_embedding)
        event_embedding_np = np.array(event_embedding)
        
        # If using GPU and tensor operations are beneficial
        if device.type != "cpu" and isinstance(user_embedding_np, np.ndarray) and isinstance(event_embedding_np, np.ndarray):
            # Convert to PyTorch tensors for GPU acceleration
            user_tensor = torch.tensor(user_embedding_np, device=device)
            event_tensor = torch.tensor(event_embedding_np, device=device)
            
            # Calculate distance on GPU
            distance = torch.norm(user_tensor - event_tensor).item()
            threshold = 0.6  # Adjust based on testing
            
            if distance < threshold:
                return image_file
        else:
            # Fall back to CPU comparison
            match = face_recognition.compare_faces([user_embedding_np], event_embedding_np, tolerance=0.5)
            if any(match):
                return image_file
    except Exception as e:
        print(f"Error in comparison: {e}")
    return None

async def finding_nemo(user_email, event_name):
    """Find all images containing the user in an event"""
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

    # For comparison, we'll use a hybrid approach
    results = []
    
    # If GPU is available and we have enough data to warrant GPU use
    if device.type != "cpu" and len(event_embeddings_list) > 20:
        print("Using GPU acceleration for comparison")
        
        # Process in smaller batches for GPU efficiency
        batch_size = 50
        for i in range(0, len(event_embeddings_list), batch_size):
            batch = event_embeddings_list[i:i+batch_size]
            
            # Process this batch on GPU
            for img, emb in batch:
                result = compare_nemo(user_embedding, img, emb)
                if result:
                    results.append(result)
    else:
        # Use CPU multiprocessing for smaller datasets or when GPU is unavailable
        print("Using CPU multiprocessing for comparison")
        num_workers = min(multiprocessing.cpu_count(), len(event_embeddings_list))
        num_workers = num_workers - 1 if num_workers > 1 else 1
        num_workers = max(2, num_workers)

        with multiprocessing.Pool(num_workers) as pool:
            loop = asyncio.get_running_loop()
            results = await loop.run_in_executor(
                None,
                lambda: list(filter(None, pool.starmap(compare_nemo, 
                                                      [(user_embedding, img, emb[0] if isinstance(emb, list) and emb else emb) 
                                                       for img, emb in event_embeddings_list])))
            )

    return results