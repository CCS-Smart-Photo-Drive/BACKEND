from BACKEND.EVENT_MANAGER_ROUTES.events import log_debug
from FACE_MODEL import play
import asyncio
import os
from BACKEND.init_config import events_collection
from google.cloud import storage
import time

# Google Cloud Storage Setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_PATH = os.path.join(BASE_DIR, "BACKEND", "config", "serviceAccount.json")
client = storage.Client.from_service_account_json(SERVICE_ACCOUNT_PATH)
bucket = client.bucket("ccs-host.appspot.com")

# async def upload_to_gcs(event_folder, event_name):
#     """Upload files to Google Cloud Storage with improved concurrency."""
#     try:
#         log_debug(f"Starting GCS upload for event: {event_name}")
#         urls = []
#         upload_tasks = []
#         bucket_name = bucket.name

#         # Count files to upload
#         files = [f for f in os.listdir(event_folder) if os.path.isfile(os.path.join(event_folder, f))]
#         log_debug(f"Found {len(files)} files to upload in {event_folder}")

#         # Prepare upload tasks
#         for image_file in files:
#             image_path = os.path.join(event_folder, image_file)
#             blob_name = f"upload_folder/{event_name}/{image_file}"
#             print(blob_name)
#             blob = bucket.blob(blob_name)

#             log_debug(f"Preparing upload for file: {image_file}")
#             upload_task = asyncio.create_task(
#                 asyncio.to_thread(blob.upload_from_filename, image_path)
#             )
#             upload_tasks.append(upload_task)
#             urls.append(f"https://storage.googleapis.com/{bucket_name}/{blob_name}")

#         # Wait for all uploads to complete
#         log_debug(f"Starting concurrent upload of {len(upload_tasks)} files")
#         start_time = time.time()
#         await asyncio.gather(*upload_tasks)
#         upload_time = time.time() - start_time
#         log_debug(f"All files uploaded successfully in {upload_time:.2f} seconds")

#         # Make files public concurrently
#         log_debug("Making uploaded files public")
#         public_tasks = []
#         for url in urls:
#             blob_name = url.replace(f"https://storage.googleapis.com/{bucket_name}/", "")
#             blob = bucket.blob(blob_name)
#             public_tasks.append(asyncio.to_thread(blob.make_public))

#         await asyncio.gather(*public_tasks)
#         log_debug("All files made public successfully")

#         return urls, None
#     except Exception as e:
#         log_debug(f"Error in GCS upload: {str(e)}")
#         return None, str(e)


async def upload_file(blob, image_path, semaphore):
    async with semaphore:
        await asyncio.to_thread(blob.upload_from_filename, image_path)

async def make_public(blob, semaphore):
    async with semaphore:
        await asyncio.to_thread(blob.make_public)

async def upload_to_gcs(event_folder, event_name, max_concurrent=3):
    """Upload files to Google Cloud Storage with limited concurrency."""
    try:
        log_debug(f"Starting GCS upload for event: {event_name}")
        urls = []
        upload_tasks = []
        public_tasks = []
        bucket_name = bucket.name
        semaphore = asyncio.Semaphore(max_concurrent)

        # Count files to upload
        files = [f for f in os.listdir(event_folder) if os.path.isfile(os.path.join(event_folder, f))]
        log_debug(f"Found {len(files)} files to upload in {event_folder}")

        # Prepare upload tasks
        for image_file in files:
            image_path = os.path.join(event_folder, image_file)
            blob_name = f"upload_folder/{event_name}/{image_file}"
            blob = bucket.blob(blob_name)
            
            log_debug(f"Preparing upload for file: {image_file}")
            upload_tasks.append(upload_file(blob, image_path, semaphore))
            urls.append(f"https://storage.googleapis.com/{bucket_name}/{blob_name}")

        # Wait for uploads to complete
        log_debug(f"Starting concurrent upload of {len(upload_tasks)} files with max {max_concurrent} at a time")
        start_time = time.time()
        await asyncio.gather(*upload_tasks)
        upload_time = time.time() - start_time
        log_debug(f"All files uploaded successfully in {upload_time:.2f} seconds")

        # Make files public concurrently
        log_debug("Making uploaded files public")
        for url in urls:
            blob_name = url.replace(f"https://storage.googleapis.com/{bucket_name}/", "")
            blob = bucket.blob(blob_name)
            public_tasks.append(make_public(blob, semaphore))

        await asyncio.gather(*public_tasks)
        log_debug("All files made public successfully")

        return urls, None
    except Exception as e:
        log_debug(f"Error in GCS upload: {str(e)}")
        return None, str(e)

async def make_it_or_break_it(image_folder: str, event_name: str, event_description: str,
                              event_organized_by: str, event_date: str, event_manager_email: str):
    try:
        # Check if the folder exists
        if not os.path.isdir(image_folder):
            raise FileNotFoundError(f"Image folder '{image_folder}' not found.")

        # # Rename images
        for idx, filename in enumerate(os.listdir(image_folder), start=1):
            file_ext = os.path.splitext(filename)[1]
            new_filename = f"{event_name}{idx}.jpg"
            old_path = os.path.join(image_folder, filename)
            new_path = os.path.join(image_folder, new_filename)
            os.rename(old_path, new_path)
        
        print(f"Renamed all images in {image_folder} with event name prefix.")
        # await clean_and_rename_images(image_folder, event_name)

        # Generate embeddings
        print(f"Embedding Generation started.")

        response = await play.generate_event_embeddings(image_folder, event_name)
        response = True

        # urls, err = await upload_to_gcs(image_folder, event_name)
        # print(urls)
        if response:
            print(f"Embedding Generation Ended.")
            event_details = {
                    "event_name": event_name,
                    "description": event_description,
                    "organized_by": event_organized_by,
                    "date": event_date,
                    "event_manager_email": event_manager_email,
                    "visible": False
                }


            try:
                res2,err = await upload_to_gcs(image_folder, event_name)
                # print(res2)
                if err:
                    print("Error Uploading images.")
                else:
                    print("successfully uploaded to gcs")
                    print(res2)
            
            except Exception as e:
                print("Failed to upload images to GCS.")
                print(e)
                return False
            try:

                res = events_collection.insert_one(event_details)
                if res:
                    print("Event details stored successfully in MongoDB.")
                    return True
            except Exception as e:
                print("Failed to store event details in MongoDB.")
                print(e)
                return False
        else:
            print("Failed to generate embeddings.")
            return False

    except Exception as e:
        print(f"Error: {e}")
        return False



a = "HackTU 6.0"
b = "Flagship Hackathon Of Thapar University"
c = "Team CCS"
d = "Sat Feb 08 2025 11:00 AM"
e = "kanavdhanda987@gmail.com"
f = "BACKEND/upload_folder/hacktu_images"

asyncio.run(make_it_or_break_it(f, a, b, c, d, e))