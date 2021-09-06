#
# Copyright (C) 2021 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
import logging

import serial

from .cosem import CosemConfig
from .hdlc_dlms_parser import HdlcDlmsParser
from .meter import Meter
from .serial_reader import SerialConfig, SerialReader

LOGGER = logging.getLogger("smartmeter")


class IskraAM550(Meter):
    HDLC_FLAG = b"\x7e"

    def __init__(self, port: str) -> None:
        super().__init__()

        serial_config = SerialConfig(
            port=port,
            baudrate=115200,
            data_bits=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stop_bits=serial.STOPBITS_ONE,
            termination=IskraAM550.HDLC_FLAG
        )
        self._serial = SerialReader(serial_config, self._data_received)
        cosem_config = CosemConfig(
            id_obis="0.0.42.0.0.255",  # TODO: set correct OBIS
            clock_obis="0.0.1.0.0.255",  # TODO: set correct OBIS
            register_obis=[]
        )
        self._parser = HdlcDlmsParser(cosem_config)

    async def start(self) -> None:
        await self._serial.start_and_listen()

    def _data_received(self, received_data: bytes) -> None:
        if not received_data:
            return
        if received_data == self.HDLC_FLAG:
            self._parser.append_to_hdlc_buffer(received_data)
            return
        self._parser.append_to_hdlc_buffer(received_data)
        if self._parser.extract_data_from_hdlc_frames():
            dlms_objects = self._parser.parse_to_dlms_objects()
            LOGGER.debug(dlms_objects)
