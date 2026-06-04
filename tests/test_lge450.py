#
# Copyright (C) 2024 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
import pytest
from pytest_mock.plugin import MockerFixture

from smartmeter_datacollector.smartmeter.lge450 import LGE450
from smartmeter_datacollector.smartmeter.meter_data import MeterDataBundle, MeterDataPointTypes
from tests.conftest import split_hex_data_to_frames
from tests.testdata.lg_e450 import UNENCRYPTED_VALID_DATA, UNENCRYPTED_VALID_DATA_CFG2026


@pytest.mark.asyncio
async def test_lge450_initialization(mocker: MockerFixture):
    observer = mocker.stub()
    test_bytes = bytes([1, 2, 3])
    serial_mock = mocker.patch("smartmeter_datacollector.smartmeter.meter.SerialReader",
                               autospec=True).return_value
    meter = LGE450("/test/port")
    serial_mock.start_and_listen.side_effect = lambda: meter._data_received(test_bytes)
    meter.register(observer)
    await meter.start()

    serial_mock.start_and_listen.assert_awaited_once()
    observer.assert_not_called()


@pytest.mark.asyncio
async def test_lge450_parse_and_provide_unencrypted_data(mocker: MockerFixture):
    observer = mocker.stub("collector_mock")
    observer.mock_add_spec(['notify'])
    serial_mock = mocker.patch("smartmeter_datacollector.smartmeter.meter.SerialReader",
                               autospec=True).return_value
    meter = LGE450("/test/port")
    meter.register(observer)
    frames = split_hex_data_to_frames(UNENCRYPTED_VALID_DATA)

    def data_received():
        for frame in frames:
            meter._data_received(frame)
    serial_mock.start_and_listen.side_effect = data_received

    await meter.start()

    serial_mock.start_and_listen.assert_awaited_once()
    observer.notify.assert_called_once()
    data_bundle = observer.notify.call_args.args[0]
    assert isinstance(data_bundle, MeterDataBundle)
    values = data_bundle.data_points
    assert any(data.type == MeterDataPointTypes.ACTIVE_POWER_P.value for data in values)
    assert any(data.type == MeterDataPointTypes.ACTIVE_POWER_N.value for data in values)
    assert any(data.type == MeterDataPointTypes.REACTIVE_POWER_P.value for data in values)
    assert any(data.type == MeterDataPointTypes.REACTIVE_POWER_N.value for data in values)
    assert any(data.type == MeterDataPointTypes.ACTIVE_ENERGY_P.value for data in values)
    assert any(data.type == MeterDataPointTypes.ACTIVE_ENERGY_N.value for data in values)
    assert any(data.type == MeterDataPointTypes.REACTIVE_ENERGY_Q1.value for data in values)
    assert any(data.type == MeterDataPointTypes.REACTIVE_ENERGY_Q2.value for data in values)
    assert any(data.type == MeterDataPointTypes.REACTIVE_ENERGY_Q3.value for data in values)
    assert any(data.type == MeterDataPointTypes.REACTIVE_ENERGY_Q4.value for data in values)
    assert any(data.type == MeterDataPointTypes.POWER_FACTOR.value for data in values)
    assert data_bundle.source == "LGZ1030655933512"
    assert data_bundle.timestamp.astimezone().strftime(r"%m/%d/%y %H:%M:%S") == "07/06/21 14:58:18"


@pytest.mark.asyncio
async def test_lge450_do_not_provide_invalid_data(mocker: MockerFixture):
    observer = mocker.stub("collector_mock")
    observer.mock_add_spec(['notify'])
    serial_mock = mocker.patch("smartmeter_datacollector.smartmeter.meter.SerialReader",
                               autospec=True).return_value
    meter = LGE450("/test/port")
    meter.register(observer)

    data_str = ("7E A0 57 CE FF 03 13 E9 69 E0 C0 00 04 00 00 46 39 31 32 09 0C 07 E5 07 06 02 0E 08 13 FF 80 00 81 06"
                " 00 00 00 00 06 00 00 00 00 06 00 00 00 00 06 00 00 00 00 06 00 0D 88 C1 06 00 00 00 00 06 00 00 00"
                " 12 06 00 00 00 01 06 00 00 00 00 06 00 04 72 0D 12 03 E8 AD 29 7E")
    invalid_data = bytes.fromhex(data_str.replace(" ", ""))

    serial_mock.start_and_listen.side_effect = lambda: meter._data_received(invalid_data)

    await meter.start()

    serial_mock.start_and_listen.assert_awaited_once()
    observer.notify.assert_not_called()


@pytest.mark.asyncio
async def test_lge450_vse_standard(mocker: MockerFixture):
    observer = mocker.stub("collector_mock")
    observer.mock_add_spec(['notify'])
    serial_mock = mocker.patch("smartmeter_datacollector.smartmeter.meter.SerialReader", autospec=True).return_value
    meter = LGE450("/test/port")
    meter.register(observer)

    frames = split_hex_data_to_frames(UNENCRYPTED_VALID_DATA_CFG2026)

    def data_received():
        for frame in frames:
            meter._data_received(frame)

    serial_mock.start_and_listen.side_effect = data_received

    await meter.start()

    serial_mock.start_and_listen.assert_awaited_once()
    observer.notify.assert_called_once()
    data_bundle = observer.notify.call_args.args[0]
    assert isinstance(data_bundle, MeterDataBundle)
    values = data_bundle.data_points

    def point_value(point_type: MeterDataPointTypes):
        return next(data.value for data in values if data.type == point_type.value)

    assert point_value(MeterDataPointTypes.ACTIVE_POWER_P) == 28
    assert point_value(MeterDataPointTypes.ACTIVE_POWER_N) == 0
    assert point_value(MeterDataPointTypes.ACTIVE_ENERGY_P) == 482939
    assert point_value(MeterDataPointTypes.ACTIVE_ENERGY_N) == 0
    assert point_value(MeterDataPointTypes.REACTIVE_ENERGY_P) == 37
    assert point_value(MeterDataPointTypes.REACTIVE_ENERGY_N) == 344697
    assert point_value(MeterDataPointTypes.VOLTAGE_L1) == 236
    assert point_value(MeterDataPointTypes.VOLTAGE_L2) == 236
    assert point_value(MeterDataPointTypes.VOLTAGE_L3) == 0
    assert point_value(MeterDataPointTypes.CURRENT_L1) == 0.09
    assert point_value(MeterDataPointTypes.CURRENT_L2) == 0.08
    assert point_value(MeterDataPointTypes.CURRENT_L3) == 0.00
    assert data_bundle.source == "LGZ1030653520967"
    assert data_bundle.timestamp.astimezone().strftime(r"%d.%m.%Y %H:%M:%S") == "04.05.2026 11:39:21"
