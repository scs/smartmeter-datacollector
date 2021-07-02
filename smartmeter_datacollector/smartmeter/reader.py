from abc import ABC

from asyncio.queues import Queue

class Reader(ABC):
    def __init__(self) -> None:
        self._observers = []
        self._queue = Queue()

    def register(self, observer) -> None:
        self._observers.append(observer)

    def notify_observers(self, *args, **kwargs) -> None:
        for obs in self._observers:
            obs.notify(*args, **kwargs)
