from typing import AsyncIterable

from aiohttp import web
from aiohttp import multipart

from microchat.api.media import DownloadMedia, DownloadPreview, UploadMedia
from microchat.api.media import GetMediaInfo
from microchat.api.media import PartReader
from microchat.api_utils.exceptions import BadRequest

from .misc import get_access_token, get_media_access_info


CHUNK_SIZE = 65535


class MultipartReader(PartReader):
    def __init__(self, origin: multipart.BodyPartReader) -> None:
        super().__init__()
        self._origin = origin

    async def read(self) -> bytes:
        return await self._origin.read()

    async def iter_chunks(
        self, size: int = CHUNK_SIZE
    ) -> AsyncIterable[bytes]:
        chunk = await self._origin.read_chunk(size)
        while chunk:
            yield chunk
            chunk = await self._origin.read_chunk(size)


async def upload_media_params(request: web.Request) -> UploadMedia:
    access_token = get_access_token(request)
    payload = await request.multipart()
    return UploadMedia(access_token, iter_multipart(payload))


async def get_media_info_params(request: web.Request) -> GetMediaInfo:
    access_token = get_access_token(request)
    hash = request.match_info["hash"]
    return GetMediaInfo(access_token, hash)


async def download_media_params(request: web.Request) -> DownloadMedia:
    access_token, csrf_token = get_media_access_info(request)
    hash = request.match_info["hash"]
    return DownloadMedia(access_token, csrf_token, hash)


async def download_preview_params(request: web.Request) -> DownloadPreview:
    access_token, csrf_token = get_media_access_info(request)
    hash = request.match_info["hash"]
    return DownloadPreview(access_token, csrf_token, hash)


async def iter_multipart(
    parts: multipart.MultipartReader
) -> AsyncIterable[tuple[str, PartReader]]:
    async for part in parts:
        name = part.name
        reader = MultipartReader(part)
        if name is None:
            raise BadRequest
        yield name, reader
