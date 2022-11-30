from __future__ import annotations

import asyncio


class Event:
    def as_json(self) -> str:
        pass


class EventStream:

    def subscribe(self) -> EventsQueue:
        return asyncio.Queue()

    async def dispatch(self, event: Event) -> None:
        pass


class EventStreamReader:

    def __init__(self, stream: EventStream) -> None:
        self.queue = stream.subscribe()

    async def get(self) -> Event:
        return await self.queue.get()


EventsQueue = asyncio.Queue[Event]
