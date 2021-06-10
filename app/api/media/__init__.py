from aiohttp import web

from .routes import dispatcher


media_subapp = web.Application(router=dispatcher)
