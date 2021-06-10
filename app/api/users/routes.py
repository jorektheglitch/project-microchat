from aiohttp import web

from .handlers import get_self
from .handlers import get_by_id
from .handlers import search_user
from .handlers import explore_users


dispatcher = web.UrlDispatcher()

dispatcher.add_get('/self', get_self)
dispatcher.add_post('/by_id', get_by_id)
dispatcher.add_post('/explore', explore_users)
dispatcher.add_post('/search', search_user)
