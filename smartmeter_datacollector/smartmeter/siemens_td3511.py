#
# Copyright (C) 2024 IBW Technik AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, List, Optional

import aioserial
import serial

from smartmeter_datacollector.smartmeter.meter import Meter, MeterError
from smartmeter_datacollector.smartmeter.meter_data import MeterDataPoint, MeterDataPointType, MeterDataPointTypes
from smartmeter_datacollector.smartmeter.reader import Reader, ReaderError
from smartmeter_datacollector.smartmeter.serial_reader import SerialConfig

LOGGER = logging.getLogger("smartmeter")


class SiemensTD3511(Meter):
    BAUDRATE = 19200

    def __init__(self, port: str,
                 baudrate: int = BAUDRATE,
                 use_system_time: bool = False) -> None:
        super().__init__()
        serial_config = SerialConfig(
            port=port,
            baudrate=baudrate,
            data_bits=serial.SEVENBITS,
            parity=serial.PARITY_EVEN,
            stop_bits=serial.STOPBITS_ONE,
            termination=b"\r\n"
        )
        try:
            self._parser = SiemensParser(use_system_time)
            self._serial = SiemensSerialReader(serial_config, self._data_received)
        except ReaderError as ex:
            LOGGER.fatal("Unable to setup serial reader for Siemens TD3511. '%s'", ex)
            raise MeterError("Failed setting up Siemens TD3511.") from ex

        LOGGER.info("Successfully set up Siemens TD3511 smart meter on '%s'.", port)

    async def start(self) -> None:
        await self._serial.start_and_listen()

    def _data_received(self, received_data: bytes) -> None:
        if not received_data:
            return
        if received_data != self._serial.TERMINATION_FLAG:
            self._parser.append_to_buffer(received_data)
            return

        data_points = self._parser.parse_data_objects()
        if not data_points:
            return
        self._notify_observers(data_points)


class SiemensSerialReader(Reader):
    """Serial reader for Siemens TD-3511. Communication is based on IEC62056-21, Mode C."""
    TERMINATION_FLAG = b'!\r\n'
    BAUDRATE_INIT = 300
    METER_ID_REQ = b'/?!\r\n'
    METER_PRG_MODE_REQ = '063036310D0A'
    METER_F001_REQ = '015232024630303103160D0A'
    METER_F009_REQ = '0152320246303039031E0D0A'

    def __init__(self, serial_config: SerialConfig, callback: Callable[[bytes], None]) -> None:
        super().__init__(callback)
        self._termination = serial_config.termination
        self._baudrate = serial_config.baudrate
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
            try:
                await asyncio.wait_for(self._enter_prg_mode(), timeout=5.0)
                while True:
                    await asyncio.wait_for(self._get_f001_dataset(), timeout=5.0)
                    await asyncio.wait_for(self._get_f009_dataset(), timeout=5.0)
            except asyncio.exceptions.TimeoutError:
                self._callback(SiemensSerialReader.TERMINATION_FLAG)
                LOGGER.warning("Meter dataset not received within timeout.")
                continue
        return

    async def _enter_prg_mode(self):
        LOGGER.info("Try to set meter into programming mode.")
        self._serial.baudrate = SiemensSerialReader.BAUDRATE_INIT
        await self._serial.write_async(SiemensSerialReader.METER_ID_REQ)
        meter_id = await self._serial.readline_async(size=-1)
        LOGGER.debug("Meter response to init sequence: %s", meter_id.decode())
        await asyncio.sleep(0.2)
        await self._serial.write_async(bytes.fromhex(SiemensSerialReader.METER_PRG_MODE_REQ))
        await asyncio.sleep(0.2)
        self._serial.baudrate = self._baudrate
        return

    async def _get_f001_dataset(self):
        # Read dataset F001
        await self._serial.write_async(bytes.fromhex(SiemensSerialReader.METER_F001_REQ))
        data: bytes = await self._serial.readline_async(size=-1)
        self._callback(data)
        while True:
            try:
                data: bytes = await asyncio.wait_for(self._serial.readline_async(size=-1), timeout=0.2)
                self._callback(data)
            except asyncio.exceptions.TimeoutError:
                LOGGER.debug("Finished reading dataset F001")
                self._callback(SiemensSerialReader.TERMINATION_FLAG)
                break
        return

    async def _get_f009_dataset(self):
        # Read dataset F009
        await self._serial.write_async(bytes.fromhex(SiemensSerialReader.METER_F009_REQ))
        data: bytes = await self._serial.readline_async(size=-1)
        self._callback(data)
        while True:
            try:
                data: bytes = await asyncio.wait_for(self._serial.readline_async(size=-1), timeout=0.2)
                self._callback(data)
            except asyncio.exceptions.TimeoutError:
                LOGGER.debug("Finished reading dataset F009")
                self._callback(SiemensSerialReader.TERMINATION_FLAG)
                break
        return


@dataclass
class RegisterDataPoint:
    obis: str
    data_point_type: MeterDataPointType
    scaling: float = 1.0


DEFAULT_REGISTER_MAPPING = [
    RegisterDataPoint("1.7.0", MeterDataPointTypes.ACTIVE_POWER_P.value, 1000),
    RegisterDataPoint("2.7.0", MeterDataPointTypes.ACTIVE_POWER_N.value, 1000),
    RegisterDataPoint("3.7.0", MeterDataPointTypes.REACTIVE_POWER_P.value, 1000),
    RegisterDataPoint("4.7.0", MeterDataPointTypes.REACTIVE_POWER_N.value, 1000),
    RegisterDataPoint("14.7", MeterDataPointTypes.NET_FREQUENCY.value),

    RegisterDataPoint("31.7", MeterDataPointTypes.CURRENT_L1.value),
    RegisterDataPoint("32.7", MeterDataPointTypes.VOLTAGE_L1.value),
    RegisterDataPoint("81.7.4", MeterDataPointTypes.ANGLE_UI_L1.value, 3.141592653589793 / 180),

    RegisterDataPoint("51.7", MeterDataPointTypes.CURRENT_L2.value),
    RegisterDataPoint("52.7", MeterDataPointTypes.VOLTAGE_L2.value),
    RegisterDataPoint("81.7.15", MeterDataPointTypes.ANGLE_UI_L2.value, 3.141592653589793 / 180),

    RegisterDataPoint("71.7", MeterDataPointTypes.CURRENT_L3.value),
    RegisterDataPoint("72.7", MeterDataPointTypes.VOLTAGE_L3.value),
    RegisterDataPoint("81.7.26", MeterDataPointTypes.ANGLE_UI_L3.value, 3.141592653589793 / 180),

    RegisterDataPoint("1.8.0", MeterDataPointTypes.ACTIVE_ENERGY_P.value, 1000),
    RegisterDataPoint("1.8.1", MeterDataPointTypes.ACTIVE_ENERGY_P_T1.value, 1000),
    RegisterDataPoint("1.8.2", MeterDataPointTypes.ACTIVE_ENERGY_P_T2.value, 1000),
    RegisterDataPoint("2.8.0", MeterDataPointTypes.ACTIVE_ENERGY_N.value, 1000),
    RegisterDataPoint("2.8.1", MeterDataPointTypes.ACTIVE_ENERGY_N_T1.value, 1000),
    RegisterDataPoint("2.8.2", MeterDataPointTypes.ACTIVE_ENERGY_N_T2.value, 1000),
    RegisterDataPoint("3.8.1", MeterDataPointTypes.REACTIVE_ENERGY_P.value, 1000),
    RegisterDataPoint("4.8.1", MeterDataPointTypes.REACTIVE_ENERGY_N.value, 1000),
]


class SiemensParser():
    REGEX = r"(.{3,20})\(([\d\-\.:]{3,20})[*\)](.{0,10}[^\)\r\n])?"

    def __init__(self, use_system_time: bool = False) -> None:
        self._use_system_time = use_system_time
        self._buffer = []
        self._register_obis = {r.obis: r for r in DEFAULT_REGISTER_MAPPING}

    def append_to_buffer(self, received_data):
        self._buffer.append(received_data.decode())

    def clear_buffer(self):
        self._buffer = []

    def parse_data_objects(self):
        # Extract timestamp and meter id
        timestamp = datetime.now(timezone.utc)
        meter_time = None
        meter_date = None
        meter_id = 'unknown'
        for data in self._buffer:
            result = re.search(SiemensParser.REGEX, data)
            if result is None:
                continue
            obis, value, _ = result.groups()

            # Extract meter id (common source id for all data points)
            if obis == "0.0.0":
                meter_id = value
            # Extract date and time
            try:
                if obis == "0.9.1":
                    meter_time = datetime.strptime(value, "%H:%M:%S").time()
                if obis == "0.9.2":
                    meter_date = datetime.strptime(value, "%y-%m-%d").date()
            except ValueError:
                meter_time = None
                meter_date = None
                LOGGER.warning("Invalid timestamp received: %s. Using system time instead.", value)
            if meter_date is not None and meter_time is not None and not self._use_system_time:
                timestamp = datetime.combine(meter_date, meter_time).astimezone(timezone.utc)

        # Extract register data
        data_points: List[MeterDataPoint] = []
        for data in self._buffer:
            result = re.search(SiemensParser.REGEX, data)
            if result is None:
                continue
            obis, value, _ = result.groups()

            if value is None:
                LOGGER.warning("No value received for %s.", obis)
                continue

            reg_type = self._register_obis.get(obis, None)
            if reg_type is None:
                continue
            data_point_type = reg_type.data_point_type

            try:
                scaled_value = float(value) * reg_type.scaling
            except (TypeError, ValueError, OverflowError):
                LOGGER.warning("Invalid register value '%s'. Skipping register.", str(value))
                continue

            data_points.append(MeterDataPoint(data_point_type, scaled_value, meter_id, timestamp))

        self.clear_buffer()
        return data_points
