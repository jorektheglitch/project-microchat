from aiohttp import web

from .handlers import login
from .handlers import register


dispatcher = web.UrlDispatcher()

dispatcher.add_post('/login', login)
dispatcher.add_post('/register', register)