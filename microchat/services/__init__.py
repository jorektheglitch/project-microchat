from microchat.core.jwt_manager import JWTManager
from microchat.storages import UoW

from .agents import Agents
from .auth import Auth
from .chats import Chats
from .conferences import Conferences
from .files import Files
from .general_exceptions import ServiceError  # noqa: F401


class ServiceSet:

    auth: Auth
    chats: Chats
    conferences: Conferences
    files: Files
    agents: Agents

    def __init__(self, uow: UoW, jwt_manager: JWTManager) -> None:
        self.auth = Auth(uow, jwt_manager)
        self.chats = Chats(uow)
        self.conferences = Conferences(uow)
        self.files = Files(uow)
        self.agents = Agents(uow)
