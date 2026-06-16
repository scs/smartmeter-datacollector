#
# Copyright (C) 2022 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
import pytest
from pytest_mock.plugin import MockerFixture

from smartmeter_datacollector.smartmeter.lge360 import LGE360
from smartmeter_datacollector.smartmeter.meter_data import MeterDataBundle, MeterDataPointTypes
from tests.conftest import split_hex_data_to_frames
from tests.testdata.lg_e360 import UNENCRYPTED_VALID_DATA_CFG2026


@pytest.mark.asyncio
async def test_lge360_vse_standard(mocker: MockerFixture):
    observer = mocker.stub("collector_mock")
    observer.mock_add_spec(['notify'])
    serial_mock = mocker.patch("smartmeter_datacollector.smartmeter.meter.SerialReader", autospec=True).return_value
    meter = LGE360("/test/port")
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

    assert point_value(MeterDataPointTypes.ACTIVE_POWER_P) == 11
    assert point_value(MeterDataPointTypes.ACTIVE_POWER_N) == 0
    assert point_value(MeterDataPointTypes.ACTIVE_ENERGY_P) == 21956
    assert point_value(MeterDataPointTypes.ACTIVE_ENERGY_N) == 4547
    assert point_value(MeterDataPointTypes.REACTIVE_ENERGY_P) == 27256
    assert point_value(MeterDataPointTypes.REACTIVE_ENERGY_N) == 4432
    assert point_value(MeterDataPointTypes.VOLTAGE_L1) == pytest.approx(235.7)
    assert point_value(MeterDataPointTypes.VOLTAGE_L2) == 0
    assert point_value(MeterDataPointTypes.VOLTAGE_L3) == 0
    assert point_value(MeterDataPointTypes.CURRENT_L1) == pytest.approx(0.06)
    assert point_value(MeterDataPointTypes.CURRENT_L2) == 0
    assert point_value(MeterDataPointTypes.CURRENT_L3) == 0
    assert data_bundle.source == "LGZ1030163598905"
    assert data_bundle.timestamp.strftime(r"%d.%m.%Y %H:%M:%S") == "06.06.2023 15:31:20"
