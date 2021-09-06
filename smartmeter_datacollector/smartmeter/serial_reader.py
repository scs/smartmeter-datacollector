#
# Copyright (C) 2021 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
from dataclasses import dataclass
from typing import Callable

import aioserial

from .reader import Reader, ReaderError


@dataclass
class SerialConfig:
    port: str
    baudrate: int = 9600
    data_bits: int = aioserial.EIGHTBITS
    parity: str = aioserial.PARITY_NONE
    stop_bits: int = aioserial.STOPBITS_ONE
    termination: bytes = aioserial.LF


# pylint: disable=too-few-public-methods
class SerialReader(Reader):
    def __init__(self, serial_config: SerialConfig, callback: Callable[[bytes], None]) -> None:
        super().__init__(callback)
        self._termination = serial_config.termination
        try:
            self._serial = aioserial.AioSerial(
                port=serial_config.port,
                baudrate=serial_config.baudrate,
                bytesize=serial_config.data_bits,
                parity=serial_config.parity,
                stopbits=serial_config.stop_bits
            )
        except aioserial.SerialException as ex:
            raise ReaderError(ex) from ex

    async def start_and_listen(self) -> None:
        while True:
            data: bytes = await self._serial.read_until_async(self._termination, None)
            self._callback(data)
