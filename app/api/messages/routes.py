from aiohttp import web

from .handlers import get_messages
from .handlers import send_message
from .handlers import edit_message
from .handlers import delete_message
from .handlers import create_conversation
from .handlers import get_chats


dispatcher = web.UrlDispatcher()

dispatcher.add_post('/get', get_messages)
dispatcher.add_post('/send', send_message)
dispatcher.add_post('/edit', edit_message)
dispatcher.add_post('/delete', delete_message)
dispatcher.add_post('/create_conversation', create_conversation)
dispatcher.add_post('/overview', get_chats)
