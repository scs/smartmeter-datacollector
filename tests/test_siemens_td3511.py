#
# Copyright (C) 2024 IBW Technik AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
import sys
from datetime import datetime
from typing import List

import pytest
from pytest_mock.plugin import MockerFixture

from smartmeter_datacollector.smartmeter.meter_data import MeterDataPointTypes
from smartmeter_datacollector.smartmeter.siemens_td3511 import SiemensTD3511

from .utils import *


@pytest.mark.skipif(sys.version_info < (3, 8), reason="Python3.7 does not support AsyncMock.")
@pytest.mark.asyncio
async def test_siemens_td3511_initialization(mocker: MockerFixture):
    observer = mocker.stub()
    test_bytes = bytes([1, 2, 3])
    serial_mock = mocker.patch("smartmeter_datacollector.smartmeter.siemens_td3511.SiemensSerialReader",
                               autospec=True).return_value
    meter = SiemensTD3511("/test/port")
    serial_mock.start_and_listen.side_effect = meter._data_received(test_bytes)
    meter.register(observer)
    await meter.start()

    serial_mock.start_and_listen.assert_awaited_once()
    observer.assert_not_called


@pytest.fixture
def unencrypted_valid_data_siemens() -> List[bytes]:
    data_str: List[bytes] = []
    data_str.append(b'0.0.0(110002267)\r\n')
    data_str.append(b'1.8.0(31550.191*kWh)\r\n')
    data_str.append(b'1.8.1(12853.433*kWh)\r\n')
    data_str.append(b'1.8.2(18696.758*kWh)\r\n')
    data_str.append(b'2.8.0(22309.592*kWh)\r\n')
    data_str.append(b'2.8.1(16717.051*kWh)\r\n')
    data_str.append(b'2.8.2(5592.541*kWh)\r\n')
    data_str.append(b'3.8.1(68.340*kvarh)\r\n')
    data_str.append(b'4.8.1(29332.587*kvarh)\r\n')
    data_str.append(b'0.9.1(21:10:29)\r\n')
    data_str.append(b'0.9.2(24-03-21)\r\n')
    data_str.append(b'1.7.0(0.386*kW)\r\n')
    data_str.append(b'2.7.0(0.000*kW)\r\n')
    data_str.append(b'3.7.0(0.000*kvar)\r\n')
    data_str.append(b'4.7.0(0.727*kvar)\r\n')
    data_str.append(b'0.9.1(21:10:29)\r\n')
    data_str.append(b'0.9.2(24-03-21)\r\n')
    data_str.append(b'14.7(49.96*Hz)\r\n')
    data_str.append(b'32.7(238.3*V)\r\n')
    data_str.append(b'52.7(240.2*V)\r\n')
    data_str.append(b'72.7(240.0*V)\r\n')
    data_str.append(b'31.7(1.58*A)\r\n')
    data_str.append(b'51.7(1.50*A)\r\n')
    data_str.append(b'71.7(0.77*A)\r\n')
    data_str.append(b'81.7.4(-80.7*Deg)\r\n')
    data_str.append(b'81.7.15(-33.3*Deg)\r\n')
    data_str.append(b'81.7.26(-74.5*Deg)\r\n')
    data_str.append(b'!\r\n')
    return data_str


@pytest.mark.skipif(sys.version_info < (3, 8), reason="Python3.7 does not support AsyncMock.")
@pytest.mark.asyncio
async def test_siemens_td3511_parse_and_provide_unencrypted_data(mocker: MockerFixture,
                                                         unencrypted_valid_data_siemens: List[bytes]):
    observer = mocker.stub("collector_mock")
    observer.mock_add_spec(['notify'])
    serial_mock = mocker.patch("smartmeter_datacollector.smartmeter.siemens_td3511.SiemensSerialReader",
                               autospec=True).return_value
    serial_mock.TERMINATION_FLAG = b'!\r\n'
    serial_mock.timestamp=datetime.now()
    meter = SiemensTD3511("/test/port")
    meter.register(observer)

    def data_received():
        for frame in unencrypted_valid_data_siemens:
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
    assert all(data.source == "110002267" for data in values)
    assert all(data.timestamp.astimezone().strftime(r"%m/%d/%y %H:%M:%S") == "03/21/24 21:10:29" for data in values)


@pytest.fixture
def unencrypted_invalid_data_siemens() -> List[bytes]:
    data_str: List[bytes] = []
    data_str.append(b'0.0.0(110002267)\r\n')
    data_str.append(b'13.8.0(31550.191*kWh)\r\n')
    data_str.append(b'13.8.1(12853.433*kWh)\r\n')
    data_str.append(b'0.8.2(18696.758*kWh)\r\n')
    data_str.append(b'0.9.1(21:10:29)\r\n')
    data_str.append(b'0.9.2(24-03-21)\r\n')
    data_str.append(b'!\r\n')
    return data_str

@pytest.mark.skipif(sys.version_info < (3, 8), reason="Python3.7 does not support AsyncMock.")
@pytest.mark.asyncio
async def test_siemens_td3511_do_not_provide_invalid_data(mocker: MockerFixture,
                                                  unencrypted_invalid_data_siemens: List[bytes]):
    observer = mocker.stub("collector_mock")
    observer.mock_add_spec(['notify'])
    serial_mock = mocker.patch("smartmeter_datacollector.smartmeter.siemens_td3511.SiemensSerialReader",
                               autospec=True).return_value
    serial_mock.TERMINATION_FLAG = b'!\r\n'
    serial_mock.timestamp=datetime.now()
    meter = SiemensTD3511("/test/port")
    meter.register(observer)

    def data_received():
        for frame in unencrypted_invalid_data_siemens:
            meter._data_received(frame)
    serial_mock.start_and_listen.side_effect = data_received

    await meter.start()

    serial_mock.start_and_listen.assert_awaited_once()
    observer.notify.assert_not_called
