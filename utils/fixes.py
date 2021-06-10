import re
from aiohttp import web


def fix_js_contenttype_header(app: web.Application):
    JS_PATTERN = re.compile(r"(\w+\.js)")
    async def fix(request, response):
        js = re.match(JS_PATTERN, request.url.name)  # r"(\w+\.js)"
        if js:
            response.headers["Content-Type"] = "application/javascript"
        return response
    app.on_response_prepare.append(fix)
