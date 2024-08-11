from enum import StrEnum
from typing import Literal, Union


class MIMEType(StrEnum):
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


class AudiosMIME(StrEnum):
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


class ImagesMIME(StrEnum):
    GIF = "gif"                     # GIF (RFC 2045 and RFC 2046)
    JPEG = "jpeg"                   # JPEG (RFC 2045 and RFC 2046)
    PJPEG = "pjpeg"                 # JPEG
    PNG = "png"                     # Portable Network Graphics (RFC 2083)
    SVG_XML = "svg+xml"             # SVG
    TIFF = "tiff"                   # TIFF (RFC 3302)
    MS_ICON = "vnd.microsoft.icon"  # ICO
    WAP_WBMP = "vnd.wap.wbmp"       # WBMP
    WEBP = "webp"                   # WebP


class VideosMIME(StrEnum):
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


MIMESubtype = ImagesMIME | AudiosMIME | VideosMIME | str
GeneralMIMEType = Literal[
    MIMEType.APPLICATION,
    MIMEType.CHEMICAL,
    MIMEType.EXAMPLE,
    MIMEType.FONT,
    MIMEType.MESSAGE,
    MIMEType.MODEL,
    MIMEType.MULTIPART,
    MIMEType.TEXT,
]
MIMETuple = Union[
    tuple[Literal[MIMEType.IMAGE], ImagesMIME],
    tuple[Literal[MIMEType.AUDIO], AudiosMIME],
    tuple[Literal[MIMEType.VIDEO], VideosMIME],
    tuple[GeneralMIMEType | str, str],
]
