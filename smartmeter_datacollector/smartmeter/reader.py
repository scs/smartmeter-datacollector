#
# Copyright (C) 2021 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
from abc import ABC, abstractmethod
from typing import List

from .reader_data import ReaderDataPoint


class Reader(ABC):
    def __init__(self) -> None:
        self._observers = []

    def register(self, observer) -> None:
        self._observers.append(observer)

    @abstractmethod
    async def start(self) -> None:
        raise NotImplementedError()

    def _notify_observers(self, data_points: List[ReaderDataPoint]) -> None:
        for observer in self._observers:
            observer.notify(data_points)
