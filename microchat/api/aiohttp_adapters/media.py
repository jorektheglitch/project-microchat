from dataclasses import dataclass
from typing import AsyncIterable

from aiohttp import web
from aiohttp import multipart

from microchat.api_utils.exceptions import BadRequest
from microchat.api_utils.request import APIRequest


CHUNK_SIZE = 65535


class PartReader:
    def __init__(self, origin: multipart.BodyPartReader):
        self.origin = origin

    async def read(self) -> bytes:
        return await self.origin.read()

    async def iter_chunks(
        self, size: int = CHUNK_SIZE
    ) -> AsyncIterable[bytes]:
        chunk = await self.origin.read_chunk(size)
        while chunk:
            yield chunk
            chunk = await self.origin.read_chunk(size)


@dataclass
class UploadMedia(APIRequest):
    payload: AsyncIterable[tuple[str, PartReader]]


@dataclass
class MediaRequest(APIRequest):
    hash: str


@dataclass
class GetMediaInfo(MediaRequest):
    pass


@dataclass
class DownloadMedia(MediaRequest):
    pass


@dataclass
class DownloadPreview(MediaRequest):
    pass


async def upload_media_params(request: web.Request) -> UploadMedia:
    payload = await request.multipart()
    return UploadMedia(iter_multipart(payload))


async def get_media_info_params(request: web.Request) -> GetMediaInfo:
    hash = request.match_info["hash"]
    return GetMediaInfo(hash)


async def download_media_params(request: web.Request) -> DownloadMedia:
    hash = request.match_info["hash"]
    return DownloadMedia(hash)


async def download_preview_params(request: web.Request) -> DownloadPreview:
    hash = request.match_info["hash"]
    return DownloadPreview(hash)


async def iter_multipart(
    parts: multipart.MultipartReader
) -> AsyncIterable[tuple[str, PartReader]]:
    async for part in parts:
        name = part.name
        reader = PartReader(part)
        if name is None:
            raise BadRequest
        yield name, reader
