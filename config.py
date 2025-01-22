import cloudinary

cloud_name = 'your_cloud_name'
api_key = 'your_api_key'
api_secret = 'your_api_secret'

cloudinary.config(
  cloud_name = cloud_name,
  api_key = api_key,
  api_secret = api_secret,
  secure = True
)
