import os

import cloudinary
from dotenv import load_dotenv

load_dotenv()

cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
api_key = os.getenv("CLOUDINARY_API_KEY")
api_secret = os.getenv("CLOUDINARY_API_SECRET")

cloudinary.config(
  cloud_name = cloud_name,
  api_key = api_key,
  api_secret = api_secret,
  secure = True
)
