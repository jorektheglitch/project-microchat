from aiohttp import web

from .handlers import all_events


dispatcher = web.UrlDispatcher()

dispatcher.add_get('/', all_events)
dispatcher.add_get('/all', all_events)
