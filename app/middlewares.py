from ipaddress import ip_address, ip_network
import re
import logging
from typing import Callable, Awaitable, Any

from aiohttp.web import middleware, Request, Response
from aiohttp.web import HTTPForbidden


JS_PATTERN = re.compile(r"(\w+\.js)")

Handler = Callable[[Request], Awaitable[Response]]


@middleware
async def disable_caching(request: Request, handler: Handler) -> Response:
    response: Response = await handler(request)
    response.headers["Cache-Control"] = "no-cache"
    return response


@middleware
async def server_timing(request: Request, handler: Handler) -> Response:
    request['server_timing'] = []
    response = await handler(request)
    raw_timings = request.get('server_timing')
    if raw_timings:
        timings = [
            f"{desc}; dur={duration:.2f}" for desc, duration in raw_timings
        ]
        server_timing_str = ", ".join(timings)
        response.headers.update({
            "Server-Timing": server_timing_str
        })
    return response


@middleware
async def mark_js_mime(request: Request, handler: Handler) -> Response:
    response: Response = await handler(request)
    js = re.match(JS_PATTERN, request.url.name)  # r"(\w+\.js)"
    if js:
        response.content_type = "application/javascript"
        response.headers["Content-Type"] = "application/javascript"
    return response


def filter_ip(ip_range: ip_network):
    @middleware
    async def mware(request: Request, handler: Handler) -> Response:
        ip = ip_address(request.remote)
        if ip not in ip_range:
            logging.info("Request from {} denied".format(ip))
            raise HTTPForbidden(
                body="IP {} not allowed. Yggdrasil only".format(ip).encode()
            )
        return await handler(request)
    return mware
