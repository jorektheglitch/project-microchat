from typing import Callable

from aiohttp import web

from microchat.core.jwt_manager import JWTManager
from microchat.storages import UoW

from .routes import get_api_router


def api_app(
    uow_factory: Callable[[], UoW],
    jwt_manager: JWTManager
) -> web.Application:
    router = get_api_router(uow_factory, jwt_manager)
    api_app = web.Application(router=router)
    return api_app
