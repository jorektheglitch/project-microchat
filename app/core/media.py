from hashlib import sha512
from secrets import token_hex
from contextlib import contextmanager

from app.models import File, Attachment
from config import MEDIA_DIRECTORY


MEDIA_DIRECTORY.mkdir(exist_ok=True)


async def resolve(message, attach):
    file = await Attachment.resolve(message=message, file=attach)
    if not file:
        raise ValueError
    return file.File.hash, file.File.name


async def store(tmpfile):
    file_hash_hex = tmpfile.hash.hex()
    tmpfile.rename(file_hash_hex)
    file = File(
        name=tmpfile.filename,
        hash=tmpfile.hash,
        size=tmpfile.size,
        type=tmpfile.mimetype
    )
    await file.store()
    return file.id


async def load(*args, **kwargs):
    pass


@contextmanager
def tempfile():
    tmp = TemporaryFile()
    tmp.open()
    try:
        yield tmp
    finally:
        tmp.close()


class TemporaryFile:

    def __init__(self):
        hextoken = token_hex(96)
        self.__path = MEDIA_DIRECTORY / hextoken
        self.__filename = None
        self.__type = "application/octet-stream"
        self.__lenght = 0
        self.__real = True
        self.__fd = None
        self.__hash = sha512()

    def open(self):
        if self.__fd is None:
            self.__fd = self.__path.open(mode="ab+")

    def close(self):
        if self.__fd is not None:
            self.__fd.close()
            self.__fd = None

    def append_content(self, content):
        self.__hash.update(content)
        self.__lenght += len(content)
        self.__fd.write(content)

    def rename(self, new_name):
        path = MEDIA_DIRECTORY / new_name
        if self.__fd:
            self.__fd.close()
        if not path.exists():
            self.__path.rename(path)
        else:
            self.__path.unlink()
        self.__path = path
        if self.__fd:
            self.__fd = path.open("ab+")

    @property
    def filename(self):
        return self.__filename

    @filename.setter
    def filename(self, filename: str):
        self.__filename = filename

    @property
    def mimetype(self):
        return self.__type

    @mimetype.setter
    def mimetype(self, type):
        self.__type = type

    @property
    def size(self):
        return self.__lenght

    @property
    def hash(self):
        return self.__hash.digest()

    def is_real(self):
        return self.__real
