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
from microchat.api.conferences import list_chat_members, add_chat_member, get_chat_member, remove_chat_member
from microchat.api.conferences import get_chat_member_permissions, edit_chat_member_permissions
from microchat.api.entities import get_self, edit_self, remove_self
from microchat.api.entities import get_entity, edit_entity, remove_entity
from microchat.api.entities import list_entity_avatars, get_entity_avatar, set_entity_avatar, remove_entity_avatar
from microchat.api.entities import get_entity_permissions, edit_entity_permissions
from microchat.api.media import store, get_media_info, get_content, get_preview

from .rendering import renderer
from .api_adapters import auth
from .api_adapters import chats
from .api_adapters import conferences
from .api_adapters import entities
from .api_adapters import media


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
    _add_auth_routes(routes)
    _add_chats_routes(routes)
    _add_conferences_routes(routes)
    _add_entities_routes(routes)
    _add_media_routes(routes)
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


def _add_conferences_routes(router: APIEndpoints) -> None:
    for path in r"/{entity_id:\d+}", r"/@{alias:\w+}":
        members_path = f"{path}/members"
        router.add_route(
            "GET", members_path,
            list_chat_members, conferences.members_request_params
        )
        router.add_route(
            "POST", members_path,
            add_chat_member, conferences.member_add_params
        )
        member_path = members_path + r"/{member_no:\d+}"
        router.add_route(
            "GET", member_path,
            get_chat_member, conferences.member_request_params
        )
        router.add_route(
            "DELETE", member_path,
            remove_chat_member, conferences.member_remove_params
        )
        permissions_path = f"{member_path}/permissions"
        router.add_route(
            "GET", permissions_path,
            get_chat_member_permissions, conferences.member_permissions_request_params
        )
        router.add_route(
            "PATCH", permissions_path,
            edit_chat_member_permissions, conferences.member_permissions_edit_params
        )


def _add_entities_routes(router: APIEndpoints) -> None:
    router.add_route("GET", "/entities/self", get_self, entities.self_request_params)
    router.add_route("PATCH", "/entities/self", edit_self, entities.self_edit_params)
    router.add_route("DELETE", "/entities/self", remove_self, entities.self_remove_params)
    for entity_path in r"/entities/{entity_id:\d+}", r"/entities/@{alias:\w+}":
        router.add_route("GET", entity_path, get_entity, entities.entity_request_params)
        router.add_route("PATCH", entity_path, edit_entity, entities.entity_edit_params)
        router.add_route("DELETE", entity_path, remove_entity, entities.entity_remove_params)
        avatars_path = f"{entity_path}/avatars"
        router.add_route("GET", avatars_path, list_entity_avatars, entities.avatars_request_params)
        router.add_route("POST", avatars_path, set_entity_avatar, entities.avatar_set_params)
        avatar_path = avatars_path + r"{id:\d+}"
        router.add_route("GET", avatar_path, get_entity_avatar, entities.avatar_request_params)
        router.add_route("DELETE", avatar_path, remove_entity_avatar, entities.avatar_delete_params)
        permissions_path = f"{entity_path}/permissions"
        router.add_route("GET", permissions_path, get_entity_permissions, entities.permissions_request_params)
        router.add_route("PATCH", permissions_path, edit_entity_permissions, entities.permissions_edit_params)


def _add_media_routes(router: APIEndpoints) -> None:
    router.add_route("POST", "/media/", store, media.upload_media_params)
    router.add_route("GET", r"/media/{hash:[\da-fA-F]+}", get_media_info, media.get_media_info_params)
    router.add_route("GET", r"/media/{hash:[\da-fA-F]+}/content", get_content, media.download_media_params)
    router.add_route("GET", r"/media/{hash:[\da-fA-F]+}/preview", get_preview, media.download_preview_params)


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
