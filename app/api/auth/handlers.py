from aiohttp import web

from app.core import users
from errors import UsernameOccupied


async def login(request: web.Request):
    data = await request.json()
    username = data.get("username")
    hexdigest = data.get("digest")
    try:
        token = await users.login(username, hexdigest)
    except ValueError as e:
        return web.json_response({
            "status": 1,
            "error": "ValueError: {}".format(e)
        })
    response = web.json_response({
        "status": 0,
        "result": {
            "id": None,
            "name": username,
            "token": token
        }
    })
    response.set_cookie('Authorization', token)
    return response


async def register(request: web.Request):
    data = await request.json()
    username = data.get('username')
    password = data.get('password')
    if not password:
        return web.json_response({
            "status": 1,
            "error": "password is missing or incorrect"
        })
    if not username:
        return web.json_response({
            "status": 1,
            "error": "name is missing or incorrect"
        })
    try:
        user = await users.register(username, password)
        token = await user.get_token()
    except UsernameOccupied:
        raise web.HTTPTemporaryRedirect('/register')
    response = web.json_response({
        "status": 0,
        "result": {
            "id": user.id,
            "name": user.username,
            "token": token
        }
    })
    response.set_cookie('Authorization', token)
    return response
