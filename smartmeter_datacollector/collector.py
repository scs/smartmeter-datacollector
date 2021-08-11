#
# Copyright (C) 2021 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
import asyncio
import logging
from asyncio.queues import QueueFull
from typing import List

from sinks.data_sink import DataSink
from smartmeter.reader_data import ReaderDataPoint

LOGGER = logging.getLogger("collector")


class Collector:
    def __init__(self) -> None:
        self._queue = asyncio.Queue()
        self._data_sinks: List[DataSink] = []

    def register_sink(self, sink: DataSink) -> None:
        assert isinstance(sink, DataSink)
        self._data_sinks.append(sink)

    def notify(self, reader_data_points: List[ReaderDataPoint]) -> None:
        for point in reader_data_points:
            try:
                self._queue.put_nowait(point)
            except QueueFull:
                LOGGER.warning("Queue is full. Current data points are dropped.")
                return

    async def process_queue(self) -> None:
        while True:
            data_point: ReaderDataPoint = await self._queue.get()
            for sink in self._data_sinks:
                await sink.send(data_point)
