from abc import ABC, abstractmethod
from dataclasses import dataclass

from typing import AsyncIterable

from microchat.api_utils.handler import authenticated, cookie_authenticated

from microchat.services import ServiceSet
from microchat.core.entities import Animation, Image, Media, User, Video

from microchat.api_utils.request import AuthenticatedRequest, CookieAuthenticatedRequest  # noqa
from microchat.api_utils.response import HEADER, APIResponse, Status
from microchat.api_utils.exceptions import BadRequest, NotFound


CHUNK_SIZE = 65535


class PartReader(ABC):

    @abstractmethod
    async def read(self) -> bytes:
        pass

    @abstractmethod
    async def iter_chunks(
        self, size: int = CHUNK_SIZE
    ) -> AsyncIterable[bytes]:
        yield b""


@dataclass
class MediaAPIRequest(AuthenticatedRequest):
    pass


@dataclass
class UploadMedia(MediaAPIRequest):
    payload: AsyncIterable[tuple[str, PartReader]]


@dataclass
class MediaRequest(MediaAPIRequest):
    hash: str


@dataclass
class GetMediaInfo(MediaRequest):
    pass


@dataclass
class DownloadMedia(MediaRequest, CookieAuthenticatedRequest):
    pass


@dataclass
class DownloadPreview(MediaRequest, CookieAuthenticatedRequest):
    pass


# @router.post("/")
@authenticated
async def store(
    request: UploadMedia,
    services: ServiceSet,
    user: User
) -> APIResponse[Media]:
    file_name = None
    file_type = None
    async with services.files.tempfile() as tempfile:
        async for name, reader in request.payload:
            if name == 'filename':
                content = await reader.read()
                file_name = content.decode()
            if name == 'mimetype':
                content = await reader.read()
                file_type = content.decode()
            if name == 'content':
                async for chunk in reader.iter_chunks():
                    await tempfile.write(chunk)
        if not (file_name and file_type):
            raise BadRequest("file name does not specified")
        media = await services.files.materialize(
            user, tempfile, file_name, file_type
        )
    return APIResponse(media, Status.CREATED)


# @router.get(r"/{hash:[\da-fA-F]+}")
@authenticated
async def get_media_info(
    request: GetMediaInfo, services: ServiceSet, user: User
) -> APIResponse[Media]:
    hash = request.hash
    media = await services.files.get_info(user, hash)
    return APIResponse(media)


# @router.get(r"/{hash:[\da-fA-F]+}/content")
@cookie_authenticated
async def get_content(
    request: DownloadMedia, services: ServiceSet, user: User
) -> APIResponse[AsyncIterable[bytes]]:
    hash = request.hash
    media = await services.files.get_info(user, hash)
    headers = {}
    disposition = f"attachment; filename={media.name}"
    headers[HEADER.ContentDisposition] = disposition
    headers[HEADER.ContentType] = f"{media.type}/{media.subtype}"
    content = services.files.iter_content(
        user, media.file_info, chunk_size=1024**2
    )
    return APIResponse(content, headers=headers)


# @router.get(r"/{hash:[\da-fA-F]+}/preview")
@cookie_authenticated
async def get_preview(
    request: DownloadPreview, services: ServiceSet, user: User
) -> APIResponse[AsyncIterable[bytes]]:
    hash = request.hash
    media = await services.files.get_info(user, hash)
    if not isinstance(media, (Image, Video, Animation)):
        media_type = type(media).__name__
        raise NotFound(f"Preview for '{media_type}' is unavailable")
    preview = media.preview
    headers = {}
    headers[HEADER.ContentDisposition] = "inline"
    headers[HEADER.ContentType] = f"{preview.type}/{preview.subtype}"
    content = services.files.iter_content(
        user, preview.file_info, chunk_size=1024**2
    )
    return APIResponse(content, headers=headers)
