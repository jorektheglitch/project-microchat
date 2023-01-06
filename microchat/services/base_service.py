from abc import ABC

from microchat.storages import UoW


class Service(ABC):
    uow: UoW

    def __init__(self, uow: UoW) -> None:
        super().__init__()
        self.uow = uow
