import asyncio
from typing import List, Dict, Set, Callable

from .events import MessageReceive, MessageDelete
from .events import ChatCreate, ChatDelete
from .events import NewUser, UserOnline, UserOffline, UserDelete
from .events import SSEStart, SSEEnd
from .events import PollingStart, PollingRequest, PollingEnd


sse_event_types = (
    MessageReceive, MessageDelete,
    ChatCreate, ChatDelete,
    NewUser, UserOnline, UserOffline, UserDelete,
    SSEStart, SSEEnd,
    PollingStart, PollingRequest, PollingEnd
)


def event_emitter(event, method=False, prefire=False) -> Callable:

    def extract_args(args):
        if method:
            _, *args = args
        return args

    def wrapper(coro: Callable) -> Callable:

        async def wrapped(*args, **kwargs):
            e_args = extract_args(args)
            result = await coro(*args, **kwargs)
            if event is MessageReceive:
                message, attachments = result
                time = message.time_sent
                kwargs['time_sent'] = time.timestamp()
            await event.emit(*e_args, **kwargs)
            return result

        async def wrapped_prefire(*args, **kwargs):
            e_args = extract_args(args)
            await event.emit(*e_args, **kwargs)
            return await coro(*args, **kwargs)

        if prefire:
            return wrapped_prefire
        return wrapped

    return wrapper


class ServerSentEventsAPI:

    __no_init = False

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super().__new__(cls)
        else:
            cls.__no_init = True
        return cls.instance

    def __init__(self):
        if self.__no_init:
            return
        self.events_queues = {
            event_type: asyncio.Queue() for event_type in sse_event_types
        }
        self.listener_queues: Dict[int, Set[asyncio.Queue]] = {}
        self.ensures: List[asyncio.Task] = []
        self.is_working = True
        self._init_handlers()
        self.start()

    def _init_handlers(self) -> None:
        for event_type, queue in self.events_queues.items():
            event_type.add_handler(queue.put)

    def start(self):
        self.is_working = True
        for queue in self.events_queues.values():
            ensure = asyncio.ensure_future(self.queue_processor(queue))
            self.ensures.append(ensure)

    async def queue_processor(self, events_queue):
        EMPTY = set()
        while self.is_working:
            event = await events_queue.get()
            if isinstance(event, MessageReceive):
                queues = set()
                sender = int(event.sender)
                receiver = int(event.receiver)
                queues.update(self.listener_queues.get(sender, EMPTY))
                queues.update(self.listener_queues.get(receiver, EMPTY))
                for queue in queues:
                    await queue.put(event)
            elif event is None:
                break

    def get_events_queue(self, user_id) -> asyncio.Queue:
        user_queues: set = self.listener_queues.setdefault(user_id, set())
        queue = asyncio.Queue()
        user_queues.add(queue)
        return queue

    async def del_events_queue(self, user_id, queue) -> None:
        user_queues: set = self.listener_queues.setdefault(user_id, set())
        user_queues.discard(queue)
        while not queue.empty():
            _ = await queue.get()

    async def stop(self):
        self.is_working = False
        for queue in self.events_queues.values():
            await queue.put(None)
        await asyncio.gather(*self.ensures)
        self.ensures.clear()
