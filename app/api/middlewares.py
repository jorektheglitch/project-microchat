import traceback

from aiohttp import web

from app.middlewares import Handler


@web.middleware
async def errors_handling(
    request: web.Request,
    handler: Handler
) -> web.Response:
    try:
        return await handler(request)
    except Exception as e:
        status_code = 500
        if isinstance(e, (ValueError, TypeError)):
            status_code = 400
        tb = traceback.format_exc()
        return web.json_response({
                "status": 1,
                "error": e.__class__.__name__,
                "description": str(e),
                "traceback": tb
            },
            status=status_code
        )
