from aiohttp import web

from .routes import dispatcher


sse_subapp = web.Application(router=dispatcher)
