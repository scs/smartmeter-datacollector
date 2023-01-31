#
# Copyright (C) 2022 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
import configparser
import json
import sys
from datetime import datetime

import pytest
from pytest_mock.plugin import MockerFixture

from smartmeter_datacollector.sinks.logger_sink import LoggerSink
from smartmeter_datacollector.smartmeter.meter_data import MeterDataPoint, MeterDataPointType

TEST_TYPE = MeterDataPointType("TEST_TYPE", "test type", "unit")

@pytest.mark.skipif(sys.version_info < (3, 8), reason="Python3.7 does not support AsyncMock.")
@pytest.mark.asyncio
async def test_logger_sink_send_point(mocker: MockerFixture):
    sink = LoggerSink("DataLogger")
    client_mock = mocker.patch.object(sink, "_logger", autospec=True)
    data_point = MeterDataPoint(TEST_TYPE, 1.0, "test_source", datetime.utcnow())

    await sink.start()
    await sink.send(data_point)

    client_mock.info.assert_called_once_with(str(data_point))

