from asyncio import Queue

from typing import AsyncIterable, Awaitable, Callable, TypeVar

from aiohttp import web
from aiohttp import typedefs

from microchat.api_utils.exceptions import APIError
from microchat.api_utils.handler import inject_services
from microchat.api_utils.request import APIRequest
from microchat.api_utils.response import APIResponse, DEFAULT_JSON_DUMPER
from microchat.api_utils.response import P, APIResponseBody, JSON

from microchat.core.events import Event
from microchat.core.jwt_manager import JWTManager
from microchat.services import ServiceError, ServiceSet
from microchat.storages import UoW

from microchat.api.auth import add_session, list_sessions, terminate_session
from microchat.api.chats import list_chats, get_chat
from microchat.api.chats import list_messages, get_message, send_message, edit_message, remove_message
from microchat.api.chats import list_chat_media, get_chat_media, remove_chat_media
from microchat.api.chats import get_attachment_content

from .rendering import renderer
from .api_adapters import auth
from .api_adapters import chats


R = TypeVar("R", bound=APIRequest, contravariant=True)


class APIEndpoints:

    def __init__(
        self,
        uow_factory: Callable[[], UoW],
        jwt_manager: JWTManager,
        renderer: Callable[[APIResponse[APIResponseBody | JSON | AsyncIterable[bytes] | Queue[Event]] | APIError], Awaitable[web.StreamResponse]]
    ) -> None:
        self.uow_factory = uow_factory
        self.jwt_manager = jwt_manager
        self.renderer = renderer
        self._router = web.UrlDispatcher()

    def add_route(
        self,
        method: str,
        route: str,
        executor: Callable[[R, ServiceSet], Awaitable[APIResponse[P]]],
        extractor: Callable[[web.Request], Awaitable[R]]
    ) -> None:
        with_services = inject_services(executor, self.uow_factory, self.jwt_manager)
        handler = endpoint(with_services, extractor, self.renderer)
        self._router.add_route(method, route, handler)


def get_api_router(
    uow_factory: Callable[[], UoW],
    jwt_manager: JWTManager
) -> web.UrlDispatcher:
    render = renderer(DEFAULT_JSON_DUMPER)
    routes = APIEndpoints(uow_factory, jwt_manager, render)
    # TODO: add all routes 
    return routes._router


def _add_auth_routes(router: APIEndpoints) -> None:
    router.add_route(
        "GET", "/auth/sessions",
        list_sessions, auth.sessions_request_params
    )
    router.add_route(
        "POST", "/auth/sessions",
        add_session, auth.session_add_params
    )
    router.add_route(
        "DELETE", r"/auth/sessions/{session_id:\w+}",
        terminate_session, auth.session_close_params
    )


def _add_chats_routes(router: APIEndpoints) -> None:
    router.add_route(
        "GET", "/chats/",
        list_chats, chats.chats_request_params
    )
    router.add_route(
        "GET", "/chats/",
        list_chats, chats.chats_request_params
    )
    for path in r"/chats/{entity_id:\d+}", r"/chats/@{alias:\w+}":
        router.add_route(
            "GET", path,
            get_chat, chats.chat_request_params
        )
    for path in r"/chats/{entity_id:\d+}/messages", r"/chats/@{alias:\w+}/messages":
        router.add_route(
            "GET", path,
            list_messages, chats.messages_request_params
        )
        router.add_route(
            "POST", path,
            send_message, chats.message_send_params
        )
        message_path = path + r"/{id:\d+}"
        router.add_route(
            "GET", message_path,
            get_message, chats.message_request_params
        )
        router.add_route(
            "PATCH", message_path,
            edit_message, chats.message_edit_params
        )
        router.add_route(
            "DELETE", message_path,
            remove_message, chats.message_delete_params
        )
        attachment_content_path = path + r"/{message_id:\d+}/attachments/{id:\w+}/content"
        router.add_route(
            "GET", attachment_content_path,
            get_attachment_content, chats.attachment_content_params
        )
        attachment_content_path = path + r"/{message_id:\d+}/attachments/{id:\w+}/preview"
        router.add_route(
            "GET", attachment_content_path,
            get_attachment_content, chats.attachment_preview_params
        )
        media_types = r"{media_type:(photo|video|audio|animation|file)s}"
        medias_path = f"{path}/{media_types}"
        router.add_route(
            "GET", medias_path,
            list_chat_media, chats.medias_request_params
        )
        media_path = medias_path + r"/{id:\d+}"
        router.add_route(
            "GET", media_path,
            get_chat_media, chats.media_request_params
        )
        router.add_route(
            "DELETE", media_path,
            remove_chat_media, chats.media_delete_params
        )


def endpoint(
    executor: Callable[[R], Awaitable[APIResponse[P]]],
    extractor: Callable[[web.Request], Awaitable[R]],
    renderer: Callable[[APIResponse[P] | APIError], Awaitable[web.StreamResponse]],
) -> typedefs.Handler:
    async def handler(request: web.Request) -> web.StreamResponse:
        api_response: APIResponse[P] | APIError
        try:
            api_request = await extractor(request)
            api_response = await executor(api_request)
        except APIError as err:
            api_response = err
        except ServiceError as service_exc:
            exc_info = APIError.from_service_exc(service_exc)
            api_response = exc_info
        reponse = await renderer(api_response)
        return reponse
    return handler
