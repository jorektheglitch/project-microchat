from aiohttp import web

from .handlers import store, load


dispatcher = web.UrlDispatcher()

dispatcher.add_post('/store', store)
dispatcher.add_get('/load', load)
