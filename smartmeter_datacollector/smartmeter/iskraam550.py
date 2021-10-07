#
# Copyright (C) 2021 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
import logging

import serial

from .cosem import Cosem, RegisterCosem
from .meter import MeterError, SerialHdlcDlmsMeter
from .meter_data import MeterDataPointTypes
from .reader import ReaderError
from .serial_reader import SerialConfig

LOGGER = logging.getLogger("smartmeter")

ISKRA_AM550_COSEM_REGISTERS = [
    RegisterCosem("1.1.1.7.0.255", MeterDataPointTypes.ACTIVE_POWER_P.value),
    RegisterCosem("1.1.2.7.0.255", MeterDataPointTypes.ACTIVE_POWER_N.value),
    RegisterCosem("1.1.3.7.0.255", MeterDataPointTypes.REACTIVE_POWER_P.value),
    RegisterCosem("1.1.4.7.0.255", MeterDataPointTypes.REACTIVE_POWER_N.value),

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


class IskraAM550(SerialHdlcDlmsMeter):
    def __init__(self, port: str, decryption_key: str = None) -> None:
        serial_config = SerialConfig(
            port=port,
            baudrate=115200,
            data_bits=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stop_bits=serial.STOPBITS_ONE,
            termination=IskraAM550.HDLC_FLAG
        )
        cosem = Cosem(
            fallback_id=port,
            register_obis=ISKRA_AM550_COSEM_REGISTERS
        )
        if decryption_key:
            LOGGER.warning("Using the Iskra AM550 meter with encrypted data has NOT BEEN TESTED yet!")
        try:
            super().__init__(serial_config, cosem, decryption_key)
        except ReaderError as ex:
            LOGGER.fatal("Unable to setup serial reader for Iskra AM550. '%s'", ex)
            raise MeterError("Failed setting up Iskra AM550.") from ex

        LOGGER.info("Successfully set up Iskra AM550 smart meter on '%s'.", port)
