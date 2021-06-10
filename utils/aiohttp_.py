from aiohttp import web


def redirect(target):
    async def handler(request: web.Request):
        raise web.HTTPFound(target)
    return handler
