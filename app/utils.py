from aiohttp import web
import logging
from time import time
from contextlib import contextmanager

from app.models import User


def is_empty(string: str):
    empty = True
    if string.strip():
        empty = False
    return empty


@contextmanager
def server_timing(request: web.Request, description: str):
    if ' ' in description:
        raise ValueError('whitespace in server timing description')
    start_time = time()
    try:
        yield
    finally:
        duration = 1000 * (time() - start_time)
        timings = request.get('server_timing', [])
        timings.append((description, duration))


def get_source_ip(request: web.Request):
    return request.remote


def auth_by_ip(handler):
    async def wrapped(request: web.Request):
        ip = get_source_ip(request)
        hexlet = ip.split(':')[0]
        if hexlet:
            dec = int(hexlet, 16)
        else:
            dec = 0
        if not (512 <= dec < 768):
            logging.info("{} doesn't allowed".format(ip))
            raise web.HTTPForbidden(
                body="IP {} not allowed. Yggdrasil only".format(ip).encode(),
            )
        async with User.session() as session:
            user = await session.execute(User._by_ip(ip))
            user = tuple(user)[0]
        if not user:
            # допилить сохранение request.rel_url чтоб красиво было
            raise web.HTTPForbidden(reason="Unregistered", body=ip.encode())
        request["user_id"], user = user
        return await handler(request)
    return wrapped
