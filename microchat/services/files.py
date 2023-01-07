from __future__ import annotations

from contextlib import asynccontextmanager

from typing import AsyncGenerator, Iterable, List

from microchat.core.entities import User, Media
from microchat.core.entities import FileInfo, TempFile, MIME_TUPLES
from microchat.core.types import MIMETuple

from .base_service import Service
from .general_exceptions import ServiceError


class UnsupportedMIMEType(ServiceError):
    pass


class Files(Service):

    async def get_info(self, user: User, hash: str) -> Media:
        return await self.uow.media.get_by_hash(user, hash)

    async def get_infos(
        self, user: User, hashes: Iterable[str]
    ) -> List[Media]:
        return await self.uow.media.get_by_hashes(user, hashes)

    async def iter_content(
        self,
        user: User,
        file: FileInfo,
        *,
        chunk_size: int = 1024**2
    ) -> AsyncGenerator[bytes, None]:
        reader = await self.uow.media.open(file)
        chunk = await reader.read(chunk_size)
        while chunk:
            yield chunk
            chunk = await reader.read(chunk_size)

    async def materialize(
        self, user: User, file: TempFile, name: str, mime_repr: str
    ) -> Media:
        mime = self._parse_mime_repr(mime_repr)
        media = await self.uow.media.save_media(user, file, name, mime)
        return media

    @asynccontextmanager
    async def tempfile(self) -> AsyncGenerator[TempFile, None]:
        tempfile = await self.uow.media.create_tempfile()
        try:
            yield tempfile
        finally:
            await tempfile.close()

    @staticmethod
    def _parse_mime_repr(mime_repr: str) -> MIMETuple:
        mime_repr_ = mime_repr.split("/", maxsplit=1)
        mime_tuple = MIME_TUPLES.get(tuple(mime_repr_))  # type: ignore
        if mime_tuple is None:
            raise UnsupportedMIMEType()
        return mime_tuple
