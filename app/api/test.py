from aiohttp import web
from aiohttp.web_exceptions import HTTPBadRequest

from utils.aiohttp_extracts import ExtractionMeta
from utils.aiohttp_extracts import MatchInfo, RequestAttr, QueryAttr

from app import models as db
from app.core.entities import User, Dialog, Conference
from app.core.auth import auth_middleware


routes = web.RouteTableDef()


@routes.view(r'/chats/{chat_id:(\d+)}{chat_type:(_\d)?}')
@routes.view(r'/chats/{chat_id:(\d+)}{chat_type:(_\d)?}/')
class Chat(web.View, metaclass=ExtractionMeta):

    async def get(
        self,
        user: RequestAttr[User],
        chat_id: MatchInfo[int],  # noqa
        chat_type: MatchInfo[str] = '_1'
    ) -> web.Response:
        if chat_id is None:
            chat_rows = await user.pm_overview()
            chats = [
                {
                    'chat': {
                        'id': chat.interlocutor,
                        'username': chat.username,
                        'chat_type': chat.type
                    },
                    'message': {
                        'sender': chat.sender,
                        'text': chat.Message.text,
                        'sent': chat.Message.time_sent.timestamp(),
                    }
                } for chat in chat_rows
            ]
            return web.json_response({'chats': chats})
        else:
            chat_id: int = int(chat_id)
            chat_type: int = int(chat_type[1:])
            conversations_types = {
                1: user.dialogs,
                2: user.conferences
            }
            conversations = conversations_types[chat_type]
            chat = await conversations[chat_id]
            chat_info = {
                'id': chat.ext_id,
                'type': chat_type,
                'username': chat.username
            }
            if isinstance(chat, Dialog):
                pass
            elif isinstance(chat, Conference):
                pass
            return web.json_response({'chat': chat_info})

    async def post(
        self,
        user: RequestAttr[User],
        chat_id: MatchInfo[int],  # noqa
        chat_type: MatchInfo[str] = '_1'
    ) -> web.Response:
        chat_id, chat_type = map(int, (chat_id, chat_type[1:]))
        if chat_id is None:
            raise HTTPBadRequest
        # chat_id, chat_type = map(int, chat_info.split('_'))
        return web.json_response({
            "chat_id": chat_id
        }, status=201)


@routes.view(r'/chats/{chat:\d+_\d}/messages')
@routes.view(r'/chats/{chat:\d+_\d}/messages/{mid:\d?|slice}')
@routes.view(r'/chats/{chat:\d+_\d}/messages/{mid:\d?|slice}/')
class ChatMessage(web.View, metaclass=ExtractionMeta):

    async def get(
        self,
        chat_info: MatchInfo['chat', str],  # noqa
        message_id: MatchInfo['mid', int],  # noqa
        user_id: RequestAttr[User],
        offset: QueryAttr[int] = 0,
        count: QueryAttr[int] = 100
    ) -> web.Response:
        chat_id, chat_type = map(int, chat_info.split('_'))
        if (not message_id) or message_id == 'slice':
            chat_id, offset, count = map(int, (chat_id, offset, count))
            messages = await get_pms(
                user_id,
                chat_id,
                offset,
                count,
                chat_type
            )
            return web.json_response({
                'chat': {'id': chat_id, 'type': chat_type},
                'messages': messages
            })
        return web.json_response({
            'chat': {'id': chat_id, 'type': chat_type},
            'message_id': message_id
        })

    async def post(self) -> web.Response:
        pass

    async def patch(self) -> web.Response:
        pass

    async def delete(self) -> web.Response:
        pass


@routes.view(r'/chats/{chat_id:\d+_\d}/users/{uid:\d*|slice}')
@routes.view(r'/chats/{chat_id:\d+_\d}/users/{uid:\d*|slice}/')
class ChatUser(web.View, metaclass=ExtractionMeta):

    async def get(self) -> web.Response:
        return web.json_response({})


test_subapp = web.Application(
    middlewares=[
        auth_middleware
    ])
test_subapp.add_routes(routes)
