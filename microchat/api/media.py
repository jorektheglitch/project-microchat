from aiohttp import web

from microchat.services import ServiceSet
from microchat.core.entities import Animation, Image, User, Video

from microchat.api_utils.response import APIResponse, Status
from microchat.api_utils.handler import api_handler, authenticated, with_services
from microchat.api_utils.exceptions import BadRequest


router = web.RouteTableDef()


@router.post("/")
@api_handler
async def store(
    request: web.Request,
    services: ServiceSet,
    user: User
) -> APIResponse:
    reader = await request.multipart()
    file_name = None
    file_type = None
    async with services.files.tempfile() as tempfile:
        async for part in reader:
            if part.name == 'filename':
                content = await part.read()
                file_name = content.decode()
            if part.name == 'mimetype':
                content = await part.read()
                file_type = content.decode()
            if part.name == 'content':
                chunk = await part.read_chunk()
                while chunk:
                    await tempfile.write(chunk)
                    chunk = await part.read_chunk()
        if not (file_name and file_type):
            raise BadRequest("file name does not specified")
        media = await services.files.materialize(
            user, tempfile, file_name, file_type
        )
    return APIResponse(media, Status.CREATED)


@router.get(r"/{hash:[\da-fA-F]+}")
@api_handler
async def get_media_info(
    request: web.Request, services: ServiceSet, user: User
) -> APIResponse:
    hash = request.match_info.get("hash")
    if not hash:
        raise web.HTTPNotFound
    media = await services.files.get_info(user, hash)
    return APIResponse(media)


@router.get(r"/{hash:[\da-fA-F]+}/content")
@with_services
@authenticated
async def get_content(
    request: web.Request, services: ServiceSet, user: User
) -> web.StreamResponse:
    hash = request.match_info.get("hash")
    if not hash:
        raise web.HTTPNotFound
    media = await services.files.get_info(user, hash)
    response = web.StreamResponse()
    disposition = f"attachment; filename={media.name}"
    response.headers["Content-Disposition"] = disposition
    response.headers["Content-Type"] = f"{media.type}/{media.subtype}"
    await response.prepare(request)
    content = services.files.iter_content(
        user, media.file_info, chunk_size=1024**2
    )
    async for chunk in content:
        await response.write(chunk)
    return response


@router.get(r"/{hash:[\da-fA-F]+}/preview")
@with_services
@authenticated
async def get_preview(
    request: web.Request, services: ServiceSet, user: User
) -> web.StreamResponse:
    hash = request.match_info.get("hash")
    if not hash:
        raise
    media = await services.files.get_info(user, hash)
    if not isinstance(media, (Image, Video, Animation)):
        raise web.HTTPNoContent()
    preview = media.preview
    response = web.StreamResponse()
    response.headers["Content-Disposition"] = "inline"
    response.headers["Content-Type"] = f"{preview.type}/{preview.subtype}"
    await response.prepare(request)
    content = services.files.iter_content(
        user, preview.file_info, chunk_size=1024**2
    )
    async for chunk in content:
        await response.write(chunk)
    return response
