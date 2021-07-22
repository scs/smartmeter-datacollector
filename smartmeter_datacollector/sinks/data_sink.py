from abc import ABC, abstractmethod

from smartmeter.reader_data import ReaderDataPoint


class DataSink(ABC):
    @abstractmethod
    async def start(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def stop(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    async def send(self, data_point: ReaderDataPoint) -> None:
        raise NotImplementedError()
