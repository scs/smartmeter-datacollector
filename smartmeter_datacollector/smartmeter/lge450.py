#
# Copyright (C) 2021 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
import logging
from typing import List

import serial

from .cosem import CosemConfig, RegisterCosem
from .hdlc_dlms_parser import HdlcDlmsParser
from .reader import Reader
from .reader_data import ReaderDataPoint, ReaderDataPointTypes
from .serial_reader import SerialConfig, SerialReader

LOGGER = logging.getLogger("smartmeter")


class LGE450(Reader):
    HDLC_FLAG = b"\x7e"

    def __init__(self, port: str, decryption_key: str = None) -> None:
        super().__init__()

        serial_config = SerialConfig(
            port=port,
            baudrate=2400,
            data_bits=serial.EIGHTBITS,
            parity=serial.PARITY_EVEN,
            stop_bits=serial.STOPBITS_ONE,
            termination=LGE450.HDLC_FLAG
        )
        self._serial = SerialReader(serial_config, self._data_received)
        cosem_config = CosemConfig(
            id_obis="0.0.42.0.0.255",
            clock_obis="0.0.1.0.0.255",
            register_obis=[
                RegisterCosem("1.0.1.7.0.255", ReaderDataPointTypes.ACTIVE_POWER_P.value),
                RegisterCosem("1.0.2.7.0.255", ReaderDataPointTypes.ACTIVE_POWER_N.value),
                RegisterCosem("1.0.3.7.0.255", ReaderDataPointTypes.REACTIVE_POWER_P.value),
                RegisterCosem("1.0.4.7.0.255", ReaderDataPointTypes.REACTIVE_POWER_N.value),
                RegisterCosem("1.1.1.8.0.255", ReaderDataPointTypes.ACTIVE_POWER_P_INT.value),
                RegisterCosem("1.1.2.8.0.255", ReaderDataPointTypes.ACTIVE_POWER_N_INT.value),
                RegisterCosem("1.0.13.7.0.255", ReaderDataPointTypes.POWER_FACTOR.value, 0.001),
            ]
        )
        self._parser = HdlcDlmsParser(cosem_config, decryption_key)

    async def start(self) -> None:
        await self._serial.start_and_listen()

    def _data_received(self, received_data: bytes) -> None:
        if not received_data:
            return
        if received_data == LGE450.HDLC_FLAG:
            self._parser.append_to_hdlc_buffer(received_data)
            return

        self._parser.append_to_hdlc_buffer(received_data)
        if self._parser.extract_data_from_hdlc_frames():
            dlms_objects = self._parser.parse_to_dlms_objects()
            data_points = self._parser.convert_dlms_bundle_to_reader_data(dlms_objects)
            self._forward_data_points(data_points)

    def _forward_data_points(self, data_points: List[ReaderDataPoint]) -> None:
        self._notify_observers(data_points)
