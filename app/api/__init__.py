from aiohttp import web

from .messages import messages_subapp
from .media import media_subapp
from .users import users_subapp
from .auth import auth_subapp
from .sse import sse_subapp
from .test import test_subapp


api = web.Application()

api.add_subapp("/messages/", messages_subapp)
api.add_subapp("/media/", media_subapp)
api.add_subapp("/users/", users_subapp)
api.add_subapp("/auth/", auth_subapp)
api.add_subapp("/events/", sse_subapp)
api.add_subapp("/test/", test_subapp)
