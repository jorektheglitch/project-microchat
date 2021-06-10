from aiohttp import web

from .routes import dispatcher


messages_subapp = web.Application(router=dispatcher)
