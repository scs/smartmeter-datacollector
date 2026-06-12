#
# Copyright (C) 2022 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
import pytest
from pytest_mock.plugin import MockerFixture

from smartmeter_datacollector.smartmeter.lge570 import LGE570
from smartmeter_datacollector.smartmeter.meter_data import MeterDataBundle, MeterDataPointTypes
from tests.conftest import split_hex_data_to_frames
from tests.testdata import lg_e570


@pytest.mark.asyncio
async def test_lge570_parse_and_provide_encrypted_data(mocker: MockerFixture):
    observer = mocker.stub("collector_mock")
    observer.mock_add_spec(['notify'])
    serial_mock = mocker.patch("smartmeter_datacollector.smartmeter.meter.SerialReader",
                               autospec=True).return_value
    meter = LGE570("/test/port", decryption_key="101112131415161718191A1B1C1D1E1F")
    meter.register(observer)
    frames = split_hex_data_to_frames(lg_e570.ENCRYPTED_VALID_DATA)

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
    assert any(data.type == MeterDataPointTypes.CURRENT_L1.value for data in values)
    assert any(data.type == MeterDataPointTypes.CURRENT_L2.value for data in values)
    assert any(data.type == MeterDataPointTypes.CURRENT_L3.value for data in values)
    assert any(data.type == MeterDataPointTypes.POWER_FACTOR.value for data in values)
    assert data_bundle.source == "LGZ1030769231253"


@pytest.mark.asyncio
async def test_lge570_vse_standard(mocker: MockerFixture):
    observer = mocker.stub("collector_mock")
    observer.mock_add_spec(['notify'])
    serial_mock = mocker.patch("smartmeter_datacollector.smartmeter.meter.SerialReader", autospec=True).return_value
    meter = LGE570("/test/port")
    meter.register(observer)

    frames = split_hex_data_to_frames(lg_e570.UNENCRYPTED_VALID_DATA_CFG2026)

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

    assert point_value(MeterDataPointTypes.ACTIVE_POWER_P) == 0
    assert point_value(MeterDataPointTypes.ACTIVE_POWER_N) == 0
    assert point_value(MeterDataPointTypes.ACTIVE_ENERGY_P) == 0
    assert point_value(MeterDataPointTypes.ACTIVE_ENERGY_N) == 0
    assert point_value(MeterDataPointTypes.REACTIVE_ENERGY_P) == 0
    assert point_value(MeterDataPointTypes.REACTIVE_ENERGY_N) == 0
    assert point_value(MeterDataPointTypes.VOLTAGE_L1) == 232
    assert point_value(MeterDataPointTypes.VOLTAGE_L2) == 0
    assert point_value(MeterDataPointTypes.VOLTAGE_L3) == 0
    assert point_value(MeterDataPointTypes.CURRENT_L1) == 0
    assert point_value(MeterDataPointTypes.CURRENT_L2) == 0
    assert point_value(MeterDataPointTypes.CURRENT_L3) == 0
    assert data_bundle.source == "LGZ1030781910790"
    assert data_bundle.timestamp.astimezone().strftime(r"%d.%m.%Y %H:%M:%S") == "04.06.2026 17:06:40"


@pytest.mark.asyncio
async def test_lge570_load_vse_standard(mocker: MockerFixture):
    observer = mocker.stub("collector_mock")
    observer.mock_add_spec(['notify'])
    serial_mock = mocker.patch("smartmeter_datacollector.smartmeter.meter.SerialReader", autospec=True).return_value
    meter = LGE570("/test/port")
    meter.register(observer)

    frames = split_hex_data_to_frames(lg_e570.UNENCRYPTED_VALID_DATA_LOAD_CFG2026)

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

    assert point_value(MeterDataPointTypes.ACTIVE_POWER_P) == 258874
    assert point_value(MeterDataPointTypes.ACTIVE_POWER_N) == 0
    assert point_value(MeterDataPointTypes.ACTIVE_ENERGY_P) == 2607383
    assert point_value(MeterDataPointTypes.ACTIVE_ENERGY_N) == 641338
    assert point_value(MeterDataPointTypes.REACTIVE_ENERGY_P) == 956364
    assert point_value(MeterDataPointTypes.REACTIVE_ENERGY_N) == 2329593
    assert point_value(MeterDataPointTypes.VOLTAGE_L1) == 229
    assert point_value(MeterDataPointTypes.VOLTAGE_L2) == 230
    assert point_value(MeterDataPointTypes.VOLTAGE_L3) == 229
    assert point_value(MeterDataPointTypes.CURRENT_L1) == 400
    assert point_value(MeterDataPointTypes.CURRENT_L2) == 200
    assert point_value(MeterDataPointTypes.CURRENT_L3) == 601
    assert data_bundle.source == "LGZ1030769231250"
    assert data_bundle.timestamp.astimezone().strftime(r"%d.%m.%Y %H:%M:%S") == "09.06.2026 16:04:40"
