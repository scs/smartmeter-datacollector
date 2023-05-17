#
# Copyright (C) 2022 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
from abc import ABC, abstractmethod
from typing import List, Optional

from .cosem import Cosem
from .hdlc_dlms_parser import HdlcDlmsParser
from .meter_data import MeterDataPoint
from .serial_reader import SerialConfig, SerialReader


class MeterError(Exception):
    pass


class Meter(ABC):
    def __init__(self) -> None:
        self._observers = []

    def register(self, observer) -> None:
        self._observers.append(observer)

    @abstractmethod
    async def start(self) -> None:
        raise NotImplementedError()

    def _notify_observers(self, data_points: List[MeterDataPoint]) -> None:
        for observer in self._observers:
            observer.notify(data_points)


class SerialHdlcDlmsMeter(Meter):
    HDLC_FLAG = b"\x7e"

    def __init__(self, serial_config: SerialConfig,
                 cosem: Cosem,
                 decryption_key: Optional[str] = None,
                 use_system_time: bool = False) -> None:
        super().__init__()
        self._parser = HdlcDlmsParser(cosem, decryption_key, use_system_time)
        self._serial = SerialReader(serial_config, self._data_received)

    async def start(self) -> None:
        await self._serial.start_and_listen()

    def _data_received(self, received_data: bytes) -> None:
        if not received_data:
            return
        if received_data == SerialHdlcDlmsMeter.HDLC_FLAG:
            self._parser.append_to_hdlc_buffer(received_data)
            return

        self._parser.append_to_hdlc_buffer(received_data)
        if self._parser.extract_data_from_hdlc_frames():
            message_time = self._parser.extract_message_time()
            dlms_objects = self._parser.parse_to_dlms_objects()
            data_points = self._parser.convert_dlms_bundle_to_reader_data(dlms_objects, message_time)
            self._notify_observers(data_points)
