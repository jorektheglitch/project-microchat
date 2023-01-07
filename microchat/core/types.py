from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum

from typing import Any, Generic, Literal, Protocol, TypeVar, Union
from typing import Awaitable, AsyncIterator, Generator, Iterable, Sequence
from typing import overload


T = TypeVar('T')
T_co = TypeVar('T_co', covariant=True)
T_contra = TypeVar('T_contra', contravariant=True)
Owner_co = TypeVar('Owner_co', covariant=True)

JSON = str | int | float | list["JSON"] | dict[str, "JSON"] | None


class MIMEType(Enum):
    APPLICATION = "application"
    AUDIO = "audio"
    CHEMICAL = "chemical"
    EXAMPLE = "example"
    FONT = "font"
    IMAGE = "image"
    MESSAGE = "message"
    MODEL = "model"
    MULTIPART = "multipart"
    TEXT = "text"
    VIDEO = "video"


class ImagesMIME(Enum):
    GIF = "gif"                     # GIF (RFC 2045 and RFC 2046)
    JPEG = "jpeg"                   # JPEG (RFC 2045 and RFC 2046)
    PJPEG = "pjpeg"                 # JPEG
    PNG = "png"                     # Portable Network Graphics (RFC 2083)
    SVG_XML = "svg+xml"             # SVG
    TIFF = "tiff"                   # TIFF (RFC 3302)
    MS_ICON = "vnd.microsoft.icon"  # ICO
    WAP_WBMP = "vnd.wap.wbmp"       # WBMP
    WEBP = "webp"                   # WebP


class VideosMIME(Enum):
    MPEG = "mpeg"                   # MPEG-1 (RFC 2045 and RFC 2046)
    MP4 = "mp4"                     # MP4 (RFC 4337)
    OGG = "ogg"                     # Ogg Theora or other (RFC 5334)
    QUICKTIME = "quicktime"         # QuickTime
    WEBM = "webm"                   # WebM
    X_MS_WMV = "x-ms-wmv"           # Windows Media Video
    X_FLV = "x-flv"                 # FLV
    X_MSVIDEO = "x-msvideo"         # AVI
    ThirdGPP = "3gpp"               # .3gpp .3gp
    ThirdGPP2 = "3gpp2"             # .3gpp2 .3g2


class AudiosMIME(Enum):
    BASIC = "basic"                 # mulaw, 8 KHz, 1 ch (RFC 2046)
    L24 = "L24"                     # 24bit Linear PCM, 8-48 KHz, 1-N ch (RFC 3190)
    MP4 = "mp4"                     # MP4
    AAC = "aac"                     # AAC
    MPEG = "mpeg"                   # MP3 or other MPEG (RFC 3003)
    OGG = "ogg"                     # Ogg Vorbis, Speex, Flac and others (RFC 5334)
    VORBIS = "vorbis"               # Vorbis (RFC 5215)
    X_MS_WMA = "x-ms-wma"           # Windows Media Audio
    X_MS_WAX = "x-ms-wax"           # Windows Media Audio перенаправление
    RN_REALAUDIO = "vnd.rn-realaudio"  # RealAudio
    WAVE = "vnd.wave"               # WAV (RFC 2361)
    WEBM = "webm"                   # WebM


MIMESubtype = ImagesMIME | AudiosMIME | VideosMIME | str
MIMETuple = Union[
    tuple[Literal[MIMEType.IMAGE], ImagesMIME],
    tuple[Literal[MIMEType.AUDIO], AudiosMIME],
    tuple[Literal[MIMEType.VIDEO], VideosMIME],
]


class AsyncSequence(Awaitable[Sequence[T]], Protocol[T]):
    @overload
    @abstractmethod
    async def __getitem__(self, index: int) -> T: ...
    @overload
    @abstractmethod
    async def __getitem__(self, index: slice) -> Sequence[T]: ...
    @abstractmethod
    async def __getitem__(self, index: int | slice) -> T | Sequence[T]: ...

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
    async def __aiter__(self) -> AsyncIterator[T]: ...

    @abstractmethod
    def __await__(self) -> Generator[None, None, Sequence[T]]: ...

    @abstractmethod
    async def append(self, value: T) -> None: ...

    @abstractmethod
    async def count(self, value: T) -> int: ...

    @abstractmethod
    async def extend(self, values: Iterable[T]) -> None: ...

    @abstractmethod
    async def index(self, value: T, start: int = ..., stop: int = ...) -> int: ...  # noqa

    @abstractmethod
    async def insert(self, index: int, value: T) -> None: ...


class Bound(ABC, Generic[T_co]):
    name: str
    owner: type

    @overload
    @abstractmethod
    def __get__(
        self: Bound[T_co], obj: None, cls: type
    ) -> Bound[T_co]: ...
    @overload  # noqa
    @abstractmethod
    def __get__(
        self, obj: T, cls: type[T]
    ) -> Awaitable[T_co]: ...

    @abstractmethod
    def __get__(
        self, obj: T | None, cls: type[T]
    ) -> Awaitable[T_co] | Bound[T_co]:
        pass

    def __set__(self, obj: T, value: Any) -> None:
        pass

    def __set_name__(self, owner: type[T], name: str) -> None:
        self.name = name
        self.owner = owner


class BoundSequence(ABC, Generic[T_co]):
    name: str
    owner: type

    @overload
    @abstractmethod
    def __get__(
        self: BoundSequence[T_co], obj: None, cls: type[T]
    ) -> BoundSequence[T_co]: ...
    @overload  # noqa
    @abstractmethod
    def __get__(
        self, obj: T, cls: type[T]
    ) -> AsyncSequence[T_co]: ...

    @abstractmethod
    def __get__(
        self, obj: T | None, cls: type[T]
    ) -> AsyncSequence[T_co] | BoundSequence[T_co]:
        pass

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = name
        self.owner = owner


class AsyncReader(ABC):

    @abstractmethod
    async def read(self, size: int = 0) -> bytes:
        pass
