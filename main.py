from BACKEND.init_config import app
from BACKEND.GENERAL_ROUTES import AboutUs, AllEvents, gen_auth
from BACKEND.USER_ROUTES import authetication, dashboard, getting_images
from BACKEND.EVENT_MANAGER_ROUTES import events, Authentication
from asgiref.wsgi import WsgiToAsgi
import uvicorn
from dotenv import load_dotenv
import os

load_dotenv()

# Convert the WSGI app to ASGI
app = WsgiToAsgi(app)



if __name__ == "__main__":
    # Run the app using Uvicorn with auto-reload enabled
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT")))
