from aiohttp import web

from app.core import users
from errors import UserDoesntExists
from app.core.auth import auth_required


@auth_required
async def get_self(request: web.Request):
    user = request['user']
    info = {
        'id': user.id,
        'name': user.username
    }
    return web.json_response({
        "status": 0,
        "result": info
    })


@auth_required
async def get_by_id(request: web.Request):
    data = await request.json()
    try:
        uid = data.get('uid')
        user = await users.get_by_id(uid)
        info = {
            'id': user.id,
            'name': user.username
        }
    except UserDoesntExists:
        info = {}
    return web.json_response({
        "status": 0,
        "result": info
    })


@auth_required
async def explore_users(request: web.Request):
    users = {}  # await db.get_users()
    return web.json_response({
        "status": 0,
        "result": dict(users)
    })


@auth_required
async def search_user(request: web.Request):
    data = await request.post()
    username = data.get('username')
    if username is None or not username:
        raise ValueError('username is missing or incorrect')
    userlist = await users.search(username)
    return web.json_response({
        "status": 0,
        "result": dict(userlist)
    })
