from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Generic, Literal, Protocol, TypeVar
from typing import Awaitable, Generator, Iterable, Sequence
from typing import overload


T = TypeVar('T')
T_co = TypeVar('T_co', covariant=True)
T_contra = TypeVar('T_contra', contravariant=True)

MIMEType = Literal[
    "application",
    "audio",
    "chemical",
    "example",
    "font",
    "image",
    "message",
    "model",
    "multipart",
    "text",
    "video"
]

ImagesMIME = Literal[
    "gif",  # GIF (RFC 2045 и RFC 2046)
    "jpeg",  # JPEG (RFC 2045 и RFC 2046)
    "pjpeg",  # JPEG[9]
    "png",  # Portable Network Graphics[10](RFC 2083)
    "svg+xml",  # SVG[11]
    "tiff",  # TIFF (RFC 3302)
    "vnd.microsoft.icon",  # ICO[12]
    "vnd.wap.wbmp",  # WBMP
    "webp",  # WebP
]

VideosMIME = Literal[
    "mpeg",  # MPEG-1 (RFC 2045 и RFC 2046)
    "mp4",  # MP4 (RFC 4337)
    "ogg",  # Ogg Theora или другое видео (RFC 5334)
    "quicktime",  # QuickTime
    "webm",  # WebM
    "x-ms-wmv",  # Windows Media Video
    "x-flv",  # FLV
    "x-msvideo",  # AVI
    "3gpp",  # .3gpp .3gp
    "3gpp2",  # .3gpp2 .3g2
]

AudiosMIME = Literal[
    "basic",  # mulaw аудио, 8 кГц, 1 канал (RFC 2046)
    "L24",  # 24bit Linear PCM аудио, 8-48 кГц, 1-N каналов (RFC 3190)
    "mp4",  # MP4
    "aac",  # AAC
    "mpeg",  # MP3 или др. MPEG (RFC 3003)
    "ogg",  # Ogg Vorbis, Speex, Flac или др. аудио (RFC 5334)
    "vorbis",  # Vorbis (RFC 5215)
    "x-ms-wma",  # Windows Media Audio
    "x-ms-wax",  # Windows Media Audio перенаправление
    "vnd.rn-realaudio",  # RealAudio
    "vnd.wave",  # WAV (RFC 2361)
    "webm",  # WebM
]


class AsyncSequence(Protocol[T]):
    @overload
    @abstractmethod
    async def __getitem__(self, index: int) -> T: ...
    @overload
    @abstractmethod
    async def __getitem__(self, index: slice) -> Sequence[T]: ...
    @abstractmethod
    async def index(self, value: T, start: int = ..., stop: int = ...) -> int: ...  # noqa
    @abstractmethod
    async def count(self, value: T) -> int: ...
    @abstractmethod
    async def __aiter__(self) -> AsyncIterator[T]: ...


class BoundSequence(ABC, Awaitable[Sequence[T]], AsyncSequence[T], Generic[T]):
    @overload
    @abstractmethod
    def __setitem__(self, index: int, value: T) -> None: ...
    @overload
    @abstractmethod
    def __setitem__(self, index: slice, values: Iterable[T]) -> None: ...
    def __setitem__(self, index: int | slice, value: T | Iterable[T]) -> None: ...  # noqa
    @overload
    @abstractmethod
    def __delitem__(self, index: int) -> None: ...
    @overload
    @abstractmethod
    def __delitem__(self, index: slice) -> None: ...
    @abstractmethod
    def __delitem__(self, index: int | slice) -> None: ...
    @abstractmethod
    async def insert(self, index: int, value: T) -> None: ...
    @abstractmethod
    async def append(self, value: T) -> None: ...
    @abstractmethod
    async def extend(self, values: Iterable[T]) -> None: ...
    @abstractmethod
    def __iadd__(self, x: Iterable[T]) -> BoundSequence[T]: ...
    @abstractmethod
    def __await__(self) -> Generator[Any, None, Sequence[T]]: ...


if __name__ == "__main__":
    pass
