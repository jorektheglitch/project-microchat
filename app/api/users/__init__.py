from aiohttp import web

from .routes import dispatcher


users_subapp = web.Application(router=dispatcher)
