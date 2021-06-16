import json
from decimal import Decimal
from functools import partial

from aiohttp import web


def redirect(target):
    async def handler(request: web.Request):
        raise web.HTTPFound(target)
    return handler


class ExtendedJSONEncoder(json.JSONEncoder):

    basic = json.JSONEncoder.default

    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return self.basic(obj)


json_dumps = partial(
    json.dumps,
    indent=2,
    cls=ExtendedJSONEncoder
)
