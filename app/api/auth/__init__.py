from aiohttp import web

from .routes import dispatcher


auth_subapp = web.Application(router=dispatcher)
