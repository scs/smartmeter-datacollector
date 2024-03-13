#
# Copyright (C) 2022 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
import sys
from typing import List

import pytest
from pytest_mock.plugin import MockerFixture

from smartmeter_datacollector.smartmeter.lge570 import LGE570
from smartmeter_datacollector.smartmeter.meter_data import MeterDataPointTypes

from .utils import *


@pytest.mark.skipif(sys.version_info < (3, 8), reason="Python3.7 does not support AsyncMock.")
@pytest.mark.asyncio
async def test_lge570_parse_and_provide_encrypted_data(mocker: MockerFixture,
                                                       encrypted_valid_data_lge570: List[bytes]):
    observer = mocker.stub("collector_mock")
    observer.mock_add_spec(['notify'])
    serial_mock = mocker.patch("smartmeter_datacollector.smartmeter.meter.SerialReader",
                               autospec=True).return_value
    meter = LGE570("/test/port", decryption_key="101112131415161718191A1B1C1D1E1F")
    meter.register(observer)

    def data_received():
        for frame in encrypted_valid_data_lge570:
            meter._data_received(frame)
    serial_mock.start_and_listen.side_effect = data_received

    await meter.start()

    serial_mock.start_and_listen.assert_awaited_once()
    observer.notify.assert_called_once()
    values = observer.notify.call_args.args[0]
    assert isinstance(values, list)
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
    assert all(data.source == "LGZ1030769231253" for data in values)
