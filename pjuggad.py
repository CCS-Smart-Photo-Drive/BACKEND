# from BACKEND.EVENT_MANAGER_ROUTES.events import log_debug
# from FACE_MODEL import play
# import asyncio
# import os
# from BACKEND.init_config import events_collection
# from google.cloud import storage
# import time
#
# # Google Cloud Storage Setup
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# SERVICE_ACCOUNT_PATH = os.path.join(BASE_DIR, "BACKEND", "config", "serviceAccount.json")
# client = storage.Client.from_service_account_json(SERVICE_ACCOUNT_PATH)
# bucket = client.bucket("ccs-host.appspot.com")
#
# # async def upload_to_gcs(event_folder, event_name):
# #     """Upload files to Google Cloud Storage with improved concurrency."""
# #     try:
# #         log_debug(f"Starting GCS upload for event: {event_name}")
# #         urls = []
# #         upload_tasks = []
# #         bucket_name = bucket.name
# #
# #         # Count files to upload
# #         files = [f for f in os.listdir(event_folder) if os.path.isfile(os.path.join(event_folder, f))]
# #         log_debug(f"Found {len(files)} files to upload in {event_folder}")
# #
# #         # Prepare upload tasks
# #         for image_file in files:
# #             image_path = os.path.join(event_folder, image_file)
# #             blob_name = f"upload_folder/{event_name}/{image_file}"
# #             print(blob_name)
# #             blob = bucket.blob(blob_name)
# #
# #             log_debug(f"Preparing upload for file: {image_file}")
# #             upload_task = asyncio.create_task(
# #                 asyncio.to_thread(blob.upload_from_filename, image_path)
# #             )
# #             upload_tasks.append(upload_task)
# #             urls.append(f"https://storage.googleapis.com/{bucket_name}/{blob_name}")
# #
# #         # Wait for all uploads to complete
# #         log_debug(f"Starting concurrent upload of {len(upload_tasks)} files")
# #         start_time = time.time()
# #         await asyncio.gather(*upload_tasks)
# #         upload_time = time.time() - start_time
# #         log_debug(f"All files uploaded successfully in {upload_time:.2f} seconds")
# #
# #         # Make files public concurrently
# #         log_debug("Making uploaded files public")
# #         public_tasks = []
# #         for url in urls:
# #             blob_name = url.replace(f"https://storage.googleapis.com/{bucket_name}/", "")
# #             blob = bucket.blob(blob_name)
# #             public_tasks.append(asyncio.to_thread(blob.make_public))
# #
# #         await asyncio.gather(*public_tasks)
# #         log_debug("All files made public successfully")
# #
# #         return urls, None
# #     except Exception as e:
# #         log_debug(f"Error in GCS upload: {str(e)}")
# #         return None, str(e)
#
# # async def upload_to_gcs(event_folder, event_name):
# #     """Upload files to Google Cloud Storage with improved concurrency."""
# #     try:
# #         print(f"Starting GCS upload for event: {event_name}")
# #         urls = []
# #         upload_tasks = []
# #         # client = storage.Client()
# #         # bucket = client.get_bucket('your-bucket-name')  # Replace with actual bucket name
# #         bucket_name = bucket.name
# #
# #         # Count files to upload
# #         files = [f for f in os.listdir(event_folder) if os.path.isfile(os.path.join(event_folder, f))]
# #         print(f"Found {len(files)} files to upload in {event_folder}")
# #
# #         # Prepare upload tasks
# #         for image_file in files:
# #             image_path = os.path.join(event_folder, image_file)
# #             blob_name = f"upload_folder/{event_name}/{image_file}"
# #             print(f"Uploading file: {blob_name}")
# #             blob = bucket.blob(blob_name)
# #
# #             upload_task = asyncio.create_task(
# #                 asyncio.to_thread(blob.upload_from_filename, image_path, timeout=300)
# #             )
# #             upload_tasks.append(upload_task)
# #             urls.append(f"https://storage.googleapis.com/{bucket_name}/{blob_name}")
# #
# #         # Wait for all uploads to complete
# #         print(f"Starting concurrent upload of {len(upload_tasks)} files")
# #         start_time = time.time()
# #         await asyncio.gather(*upload_tasks)
# #         upload_time = time.time() - start_time
# #         print(f"All files uploaded successfully in {upload_time:.2f} seconds")
# #
# #         # Make files public concurrently
# #         print("Making uploaded files public")
# #         public_tasks = []
# #         for url in urls:
# #             blob_name = url.replace(f"https://storage.googleapis.com/{bucket_name}/", "")
# #             blob = bucket.blob(blob_name)
# #             public_tasks.append(asyncio.to_thread(blob.make_public))
# #
# #         await asyncio.gather(*public_tasks)
# #         print("All files made public successfully")
# #
# #         return urls, None
# #     except Exception as e:
# #         print(f"Error in GCS upload: {str(e)}")
# #         return None, str(e)
#
# async def make_it_or_break_it(image_folder: str, event_name: str, event_description: str,
#                               event_organized_by: str, event_date: str, event_manager_email: str):
#     try:
#         # Check if the folder exists
#         if not os.path.isdir(image_folder):
#             raise FileNotFoundError(f"Image folder '{image_folder}' not found.")
#
#         # # Rename images
#         # for idx, filename in enumerate(os.listdir(image_folder), start=1):
#         #     file_ext = os.path.splitext(filename)[1]
#         #     new_filename = f"{event_name}{idx}{file_ext}"
#         #     old_path = os.path.join(image_folder, filename)
#         #     new_path = os.path.join(image_folder, new_filename)
#         #     os.rename(old_path, new_path)
#         #
#         # print(f"Renamed all images in {image_folder} with event name prefix.")
#
#         # Generate embeddings
#         # response = await play.generate_event_embeddings(image_folder, event_name)
#         response = True
#         if response:
#             event_details = {
#                     "event_name": event_name,
#                     "event_description": event_description,
#                     "event_organized_by": event_organized_by,
#                     "event_date": event_date,
#                     "event_manager_email": event_manager_email,
#                 }
#
#
#             # try:
#             #     res2 = await upload_to_gcs(image_folder, event_name)
#             #     if res2:
#             #         print("Images uploaded to GCS successfully.")
#             #
#             # except Exception as e:
#             #     print("Failed to upload images to GCS.")
#             #     print(e)
#             #     return False
#             try:
#
#                 res = await events_collection.insert_one(event_details)
#                 if res:
#                     print("Event details stored successfully in MongoDB.")
#                     return True
#             except Exception as e:
#                 print("Failed to store event details in MongoDB.")
#                 print(e)
#                 return False
#         else:
#             print("Failed to generate embeddings.")
#             return False
#
#     except Exception as e:
#         print(f"Error: {e}")
#         return False
#
#
#
# a = "HackTu"
# b = "Thapar Premier Hackathon"
# c = "Team CCS"
# d = "2025-08-02"
# e = "jsriharisesh_be24@gmail.com"
# f = "BACKEND/PHOTOS"
#
# asyncio.run(make_it_or_break_it(f, a, b, c, d, e))