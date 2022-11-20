from aiohttp import web

from microchat.api_utils import BadRequest, NotFound
from microchat.core.entities import Bot, Conference, User
from microchat.core.entities import ConferenceParticipation, Dialog
from microchat.services import ServiceSet


async def get_chat(
    services: ServiceSet,
    user: User,
    entity_id: str | int | None,
    alias: str | None
) -> Dialog | ConferenceParticipation[User]:
    if isinstance(entity_id, str):
        entity_id = int(entity_id)
        chat = await services.agents.get_chat(user, entity_id)
    elif alias:
        chat = await services.agents.resolve_chat_alias(user, alias)
    else:
        raise BadRequest
    return chat


async def get_entity(
    services: ServiceSet,
    user: User,
    entity_id: str | int | None,
    alias: str | None
) -> User | Bot | Conference:
    if isinstance(entity_id, str):
        entity_id = int(entity_id)
        entity = await services.agents.get(user, entity_id)
    elif alias:
        entity = await services.agents.resolve_alias(user, alias)
    else:
        raise BadRequest
    return entity


async def get_conference(
    services: ServiceSet,
    user: User,
    entity_id: str | int | None,
    alias: str | None
) -> Conference:
    entity = await get_entity(services, user, entity_id, alias)
    if not isinstance(entity, Conference):
        raise NotFound
    return entity


def get_offset_count(
    request: web.Request, defaults: tuple[int, int] = (0, 100)
) -> tuple[int, int]:
    default_offset, default_count = defaults
    offset = request.query.get("offset", default_offset)
    count = request.query.get("count", default_count)
    try:
        offset = int(offset)
        count = int(count)
    except (ValueError, TypeError):
        raise BadRequest("Invalid 'offset' or 'count' params")
    return offset, count
