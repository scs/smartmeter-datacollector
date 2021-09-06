#
# Copyright (C) 2021 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
import logging

from ..smartmeter.meter_data import MeterDataPoint
from .data_sink import DataSink


class LoggerSink(DataSink):
    def __init__(self, logger_name: str) -> None:
        self._logger = logging.getLogger(logger_name)
        self._logger.setLevel(logging.INFO)

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def send(self, data_point: MeterDataPoint) -> None:
        self._logger.info(str(data_point))
