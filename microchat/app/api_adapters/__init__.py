from itertools import chain
from typing import Any, Sequence

from microchat.app.route import APIRoute

from .auth import routes as auth_routes
from .chats import routes as chats_routes
from .conferences import routes as conferences_routes
from .entities import routes as entities_routes
from .events import routes as events_routes
from .media import routes as media_routes


sections: dict[str, Sequence[APIRoute[Any]]] = {
    "auth": auth_routes,
    "chats": chats_routes,
    "conferences": conferences_routes,
    "entities": entities_routes,
    "events": events_routes,
    "media": media_routes
}

routes: tuple[APIRoute[Any], ...] = tuple(chain.from_iterable(sections.values()))
