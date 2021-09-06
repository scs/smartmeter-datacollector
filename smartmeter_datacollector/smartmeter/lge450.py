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
from .meter import Meter, MeterError
from .meter_data import MeterDataPoint, MeterDataPointTypes
from .reader import ReaderError
from .serial_reader import SerialConfig, SerialReader

LOGGER = logging.getLogger("smartmeter")

LGE450_COSEM_REGISTERS = [
    RegisterCosem("1.0.1.7.0.255", MeterDataPointTypes.ACTIVE_POWER_P.value),
    RegisterCosem("1.0.2.7.0.255", MeterDataPointTypes.ACTIVE_POWER_N.value),
    RegisterCosem("1.0.3.7.0.255", MeterDataPointTypes.REACTIVE_POWER_P.value),
    RegisterCosem("1.0.4.7.0.255", MeterDataPointTypes.REACTIVE_POWER_N.value),

    RegisterCosem("1.0.13.7.0.255", MeterDataPointTypes.POWER_FACTOR.value, 0.001),
    RegisterCosem("1.0.14.7.0.255", MeterDataPointTypes.NET_FREQUENCY.value),

    RegisterCosem("1.0.21.7.0.255", MeterDataPointTypes.ACTIVE_POWER_P_L1.value),
    RegisterCosem("1.0.22.7.0.255", MeterDataPointTypes.ACTIVE_POWER_N_L1.value),
    RegisterCosem("1.0.23.7.0.255", MeterDataPointTypes.REACTIVE_POWER_P_L1.value),
    RegisterCosem("1.0.24.7.0.255", MeterDataPointTypes.REACTIVE_POWER_N_L1.value),

    RegisterCosem("1.0.31.7.0.255", MeterDataPointTypes.CURRENT_L1.value),
    RegisterCosem("1.0.32.7.0.255", MeterDataPointTypes.VOLTAGE_L1.value),

    RegisterCosem("1.0.41.7.0.255", MeterDataPointTypes.ACTIVE_POWER_P_L2.value),
    RegisterCosem("1.0.42.7.0.255", MeterDataPointTypes.ACTIVE_POWER_N_L2.value),
    RegisterCosem("1.0.43.7.0.255", MeterDataPointTypes.REACTIVE_POWER_P_L2.value),
    RegisterCosem("1.0.44.7.0.255", MeterDataPointTypes.REACTIVE_POWER_N_L2.value),

    RegisterCosem("1.0.51.7.0.255", MeterDataPointTypes.CURRENT_L2.value),
    RegisterCosem("1.0.52.7.0.255", MeterDataPointTypes.VOLTAGE_L2.value),

    RegisterCosem("1.0.61.7.0.255", MeterDataPointTypes.ACTIVE_POWER_P_L3.value),
    RegisterCosem("1.0.62.7.0.255", MeterDataPointTypes.ACTIVE_POWER_N_L3.value),
    RegisterCosem("1.0.63.7.0.255", MeterDataPointTypes.REACTIVE_POWER_P_L3.value),
    RegisterCosem("1.0.64.7.0.255", MeterDataPointTypes.REACTIVE_POWER_N_L3.value),

    RegisterCosem("1.0.71.7.0.255", MeterDataPointTypes.CURRENT_L3.value),
    RegisterCosem("1.0.72.7.0.255", MeterDataPointTypes.VOLTAGE_L3.value),

    RegisterCosem("1.0.81.7.40.255", MeterDataPointTypes.ANGLE_UI_L1.value),
    RegisterCosem("1.0.81.7.51.255", MeterDataPointTypes.ANGLE_UI_L2.value),
    RegisterCosem("1.0.81.7.62.255", MeterDataPointTypes.ANGLE_UI_L3.value),

    RegisterCosem("1.1.1.8.0.255", MeterDataPointTypes.ACTIVE_ENERGY_P.value),
    RegisterCosem("1.1.2.8.0.255", MeterDataPointTypes.ACTIVE_ENERGY_N.value),
    RegisterCosem("1.1.3.8.0.255", MeterDataPointTypes.REACTIVE_ENERGY_P.value),
    RegisterCosem("1.1.4.8.0.255", MeterDataPointTypes.REACTIVE_ENERGY_N.value),

    RegisterCosem("1.1.5.8.0.255", MeterDataPointTypes.REACTIVE_ENERGY_Q1.value),
    RegisterCosem("1.1.6.8.0.255", MeterDataPointTypes.REACTIVE_ENERGY_Q2.value),
    RegisterCosem("1.1.7.8.0.255", MeterDataPointTypes.REACTIVE_ENERGY_Q3.value),
    RegisterCosem("1.1.8.8.0.255", MeterDataPointTypes.REACTIVE_ENERGY_Q4.value),
]


class LGE450(Meter):
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
        try:
            self._serial = SerialReader(serial_config, self._data_received)
        except ReaderError as ex:
            LOGGER.fatal("Unable to setup serial reader for L+G E450. '%s'", ex)
            raise MeterError("Failed setting up L+G E450.") from ex

        cosem_config = CosemConfig(
            id_obis="0.0.42.0.0.255",
            clock_obis="0.0.1.0.0.255",
            register_obis=LGE450_COSEM_REGISTERS
        )
        self._parser = HdlcDlmsParser(cosem_config, decryption_key)
        LOGGER.info("Successfully set up L+G E450 smart meter on '%s'.", port)

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

    def _forward_data_points(self, data_points: List[MeterDataPoint]) -> None:
        self._notify_observers(data_points)
