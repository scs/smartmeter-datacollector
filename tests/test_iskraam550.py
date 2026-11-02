#
# Copyright (C) 2024 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
import pytest
from pytest_mock.plugin import MockerFixture

from smartmeter_datacollector.smartmeter.iskraam550 import IskraAM550
from smartmeter_datacollector.smartmeter.meter_data import MeterDataBundle, MeterDataPointTypes
from tests.conftest import split_hex_data_to_frames
from tests.testdata.iskra_am550 import (UNENCRYPTED_VALID_DATA, UNENCRYPTED_VALID_DATA_CFG2026,
                                        UNENCRYPTED_VALID_DATA_NO_PUSH_LIST)


@pytest.mark.asyncio
async def test_iskaam550_initialization(mocker: MockerFixture):
    observer = mocker.stub()
    test_bytes = bytes([1, 2, 3])
    serial_mock = mocker.patch("smartmeter_datacollector.smartmeter.meter.SerialReader",
                               autospec=True).return_value
    meter = IskraAM550("/test/port")
    serial_mock.start_and_listen.side_effect = lambda: meter._data_received(test_bytes)
    meter.register(observer)
    await meter.start()

    serial_mock.start_and_listen.assert_awaited_once()
    observer.assert_not_called()


@pytest.mark.asyncio
async def test_iskraam550_parse_and_provide_unencrypted_data(mocker: MockerFixture):
    observer = mocker.stub("collector_mock")
    observer.mock_add_spec(['notify'])
    serial_mock = mocker.patch("smartmeter_datacollector.smartmeter.meter.SerialReader",
                               autospec=True).return_value
    meter = IskraAM550("/test/port")
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
    assert data_bundle.source == "ISK1030775213859"
    # message time comes with timezone info (+02:00)
    assert data_bundle.timestamp.strftime(r"%m/%d/%y %H:%M:%S") == "08/15/20 04:19:45"


@pytest.mark.asyncio
async def test_iskraam550_parse_data_with_vse_standard(mocker: MockerFixture):
    observer = mocker.stub("collector_mock")
    observer.mock_add_spec(['notify'])
    serial_mock = mocker.patch("smartmeter_datacollector.smartmeter.meter.SerialReader", autospec=True).return_value
    meter = IskraAM550("/test/port")
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

    assert point_value(MeterDataPointTypes.ACTIVE_POWER_P) == 27
    assert point_value(MeterDataPointTypes.ACTIVE_POWER_N) == 0
    assert point_value(MeterDataPointTypes.ACTIVE_ENERGY_P) == 15207
    assert point_value(MeterDataPointTypes.ACTIVE_ENERGY_N) == 8987
    assert point_value(MeterDataPointTypes.REACTIVE_ENERGY_P) == 12784
    assert point_value(MeterDataPointTypes.REACTIVE_ENERGY_N) == 5654
    assert point_value(MeterDataPointTypes.VOLTAGE_L1) == pytest.approx(234.7)
    assert point_value(MeterDataPointTypes.VOLTAGE_L2) == 0
    assert point_value(MeterDataPointTypes.VOLTAGE_L3) == 0
    assert point_value(MeterDataPointTypes.CURRENT_L1) == pytest.approx(0.12)
    assert point_value(MeterDataPointTypes.CURRENT_L2) == 0
    assert point_value(MeterDataPointTypes.CURRENT_L3) == 0
    assert data_bundle.source == "ISK1030783821282"
    assert data_bundle.timestamp.strftime(r"%d.%m.%Y %H:%M:%S") == "04.05.2026 17:19:30"


@pytest.mark.asyncio
async def test_iskraam550_parse_data_without_push_object_list(mocker: MockerFixture):
    """Some AM550 deployments send no push-object-list and group each OBIS code with its value.

    Before this was supported the message was mistaken for one carrying a push-object-list --
    its first element is a structure too -- and parsing failed with
    ``ValueError: Invalid OBIS Code.``
    """
    observer = mocker.stub("collector_mock")
    observer.mock_add_spec(['notify'])
    serial_mock = mocker.patch("smartmeter_datacollector.smartmeter.meter.SerialReader", autospec=True).return_value
    meter = IskraAM550("/test/port")
    meter.register(observer)

    frames = split_hex_data_to_frames(UNENCRYPTED_VALID_DATA_NO_PUSH_LIST)

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
    assert point_value(MeterDataPointTypes.ACTIVE_POWER_N) == 6345
    assert point_value(MeterDataPointTypes.ACTIVE_ENERGY_P) == 13141364
    assert point_value(MeterDataPointTypes.ACTIVE_ENERGY_N) == 86049396
    assert point_value(MeterDataPointTypes.ACTIVE_ENERGY_P_T1) == 4293752
    assert point_value(MeterDataPointTypes.ACTIVE_ENERGY_P_T2) == 8847612
    assert point_value(MeterDataPointTypes.ACTIVE_ENERGY_N_T1) == 33140808
    assert point_value(MeterDataPointTypes.ACTIVE_ENERGY_N_T2) == 52908588
    # scaling comes from the COSEM register configuration, not from the frame's scaler/unit
    assert point_value(MeterDataPointTypes.VOLTAGE_L1) == pytest.approx(231.7)
    assert point_value(MeterDataPointTypes.CURRENT_L1) == pytest.approx(10.25)
    # the ID is an octet-string here and must be decoded, not repr'd
    assert data_bundle.source == "78447008"
    assert data_bundle.timestamp.strftime(r"%d.%m.%Y %H:%M:%S") == "06.09.2026 15:40:40"
