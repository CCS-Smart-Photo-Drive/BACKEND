from BACKEND.init_config import tokens_collection, user_collection
from bson import ObjectId
from flask import g


def path_request_auth(path):
    return path not in ['/auth_user', '/auth_admin' '/all_events', '/about_us']

def path_request_admin(path):
    return path in ['/my_events', '/add_new_event']

async def fuck_off(send):
    await send({
        "type": "http.response.start",
        "status": 401,
        "headers": [
            [b"content-type", b"text/plain"],
        ],
    })
    await send({
        "type": "http.response.body",
        "body": b"Unauthorized",
    })

class AuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # Process the incoming request (scope)
        if scope['type'] not in ['http', 'https']:
            await self.app(scope, receive, send)

        token = None
        for name, item in scope["headers"]:
            if name != b"session_authorization":
                continue
            token = item.encode("utf-8").split(" ")[1]
            break

        if not token:
            if not path_request_auth(scope['path']):
                await self.app(scope, receive, send)
                return
            return await fuck_off(send)

        data = tokens_collection.find_one({ 'token': token })
        if not data:
            return await fuck_off(send)

        user_data = user_collection.find_one({ '_id': ObjectId(data['user_id'])})
        if not user_data or (user_data['is_admin'] is False and path_request_admin(scope['path'])):
            return await fuck_off(send)

        g.user = user_data
