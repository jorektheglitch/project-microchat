import logging

from aiohttp import web
from aiohttp_remotes import setup, XForwardedStrict
from utils.fixes import fix_js_contenttype_header

from app import get_app
from config import HOST, PORT
from config import PROXIFIED, PROXY_SUBNET
from config import SERVE_STATIC, STATIC_PATH


log = logging.getLogger()
log.setLevel(logging.DEBUG)
logger_handler = logging.StreamHandler()
logger_handler.setLevel(logging.DEBUG)
log.addHandler(logger_handler)


async def app_factory() -> web.Application:
    app = await get_app()
    fix_js_contenttype_header(app)
    if SERVE_STATIC:
        app.router.add_static('/', STATIC_PATH)
    if PROXIFIED:
        await setup(
            app,
            XForwardedStrict([
                PROXY_SUBNET
            ])
        )
    return app


if __name__ == "__main__":
    web.run_app(app_factory(), host=HOST, port=PORT)
