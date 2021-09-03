#
# Copyright (C) 2021 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
from abc import ABC, abstractmethod
from typing import Callable


class ReaderError(Exception):
    pass


# pylint: disable=too-few-public-methods
class Reader(ABC):
    def __init__(self, callback: Callable[[bytes], None]) -> None:
        self._callback = callback

    @abstractmethod
    async def start_and_listen(self) -> None:
        pass
