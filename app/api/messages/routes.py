from aiohttp import web

from .handlers import get_messages
from .handlers import get_chats
from .handlers import send_message


dispatcher = web.UrlDispatcher()

dispatcher.add_post('/send', send_message)
dispatcher.add_post('/get', get_messages)
dispatcher.add_post('/overview', get_chats)
