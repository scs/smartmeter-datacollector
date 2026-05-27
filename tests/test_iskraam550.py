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
from tests.testdata.iskra_am550 import UNENCRYPTED_VALID_DATA


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
