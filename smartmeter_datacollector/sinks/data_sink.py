from abc import ABC

from smartmeter.reader_data import ReaderDataPoint


class DataSink(ABC):
    async def send(self, data_point: ReaderDataPoint) -> None:
        raise NotImplementedError()
