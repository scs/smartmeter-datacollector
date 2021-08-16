#
# Copyright (C) 2021 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
from dataclasses import dataclass

import serial
from aioserial import AioSerial


@dataclass
class SerialConfig:
    port: str
    baudrate: int = 9600
    data_bits: int = serial.EIGHTBITS
    parity: str = serial.PARITY_NONE
    stop_bits: int = serial.STOPBITS_ONE
    termination: bytes = serial.LF


# pylint: disable=too-few-public-methods
class SerialReader:
    CHUNK_SIZE = 16

    def __init__(self, serial_config: SerialConfig, callback) -> None:
        self._callback = callback
        self._termination = serial_config.termination
        self._serial = AioSerial(
            port=serial_config.port,
            baudrate=serial_config.baudrate,
            bytesize=serial_config.data_bits,
            parity=serial_config.parity,
            stopbits=serial_config.stop_bits
        )

    async def start_and_listen(self) -> None:
        while True:
            data: bytes = await self._serial.read_until_async(self._termination, None)
            self._callback(data)
