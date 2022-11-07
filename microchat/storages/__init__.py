from types import TracebackType
from typing import TypeVar, overload


T = TypeVar("T")
Exc = TypeVar("Exc", BaseException, Exception)


class UoW:

    async def __aenter__(self: T) -> T:
        return self

    @overload
    async def __aexit__(
        self,
        exc_type: type[BaseException], exc: BaseException, tb: TracebackType
    ) -> None: ...
    @overload
    async def __aexit__(self, exc_type: None, exc: None, tb: None) -> None: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None
    ) -> None:
        pass
