from aiohttp import web

from app.models.analytics import users_stats

from .middlewares import errors_handling

from .messages import messages_subapp
from .media import media_subapp
from .users import users_subapp
from .auth import auth_subapp
from .sse import sse_subapp
from .test import test_subapp


api = web.Application(middlewares=[
    errors_handling
])

api.add_subapp("/messages/", messages_subapp)
api.add_subapp("/media/", media_subapp)
api.add_subapp("/users/", users_subapp)
api.add_subapp("/auth/", auth_subapp)
api.add_subapp("/events/", sse_subapp)
api.add_subapp("/test/", test_subapp)


async def stats(request: web.Request) -> web.Response:
    raw_stats = await users_stats()
    general = raw_stats["general"]
    exact = raw_stats["exact"]
    stats = {
        "general": {
            "sended": {
                "avg": float(general.sended_avg),
                "median":  float(general.sended_med)
            },
            "received": {
                "avg": float(general.received_avg),
                "median": float(general.received_med)
            },
        },
        "exact": [
            {
                "id": row.User.id,
                "username": row.User.username,
                "sended": row.sended,
                "received": row.received
            } for row in exact
        ]
    }
    return web.json_response(stats)

api.router.add_get("/stats", stats)
