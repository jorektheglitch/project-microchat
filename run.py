import logging
from ipaddress import ip_network

from aiohttp import web
from aiohttp_remotes import setup, XForwardedStrict
from utils.fixes import fix_js_contenttype_header

from app import get_app


PROXIFIED = False

log = logging.getLogger()
log.setLevel(logging.DEBUG)
logger_handler = logging.StreamHandler()
logger_handler.setLevel(logging.DEBUG)
log.addHandler(logger_handler)


async def app_factory() -> web.Application:
    app = await get_app()
    fix_js_contenttype_header(app)
    if PROXIFIED:
        await setup(
            app,
            XForwardedStrict([
                ip_network("::/127")
            ])
        )
    return app


if __name__ == "__main__":
    web.run_app(app_factory(), host='::', port=8081)
