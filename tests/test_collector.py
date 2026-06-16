#
# Copyright (C) 2024 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
import asyncio
from datetime import datetime, timezone

import pytest
from pytest_mock import MockerFixture

from smartmeter_datacollector.collector import Collector
from smartmeter_datacollector.sinks.data_sink import DataSink
from smartmeter_datacollector.smartmeter.meter_data import MeterDataBundle, MeterDataPoint, MeterDataPointType
from smartmeter_datacollector.smartmeter.obis import OBISCode


@pytest.fixture
def test_type() -> MeterDataPointType:
    return MeterDataPointType("TEST_TYPE", "test type", "unit")


@pytest.mark.asyncio
async def test_collector_with_one_sink(mocker: MockerFixture, test_type: MeterDataPointType):
    coll = Collector()
    sink = mocker.AsyncMock(DataSink)
    data_point = MeterDataPoint(test_type, 0.0, OBISCode(0, 1, 2, 3, 4, 5))
    data_bundle = MeterDataBundle("test_source", datetime.now(timezone.utc), [data_point])

    coll.register_sink(sink)
    coll.notify(data_bundle)
    routine = coll.process_queue()

    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(routine, 0.1)

    sink.send.assert_awaited_once_with(data_bundle)


@pytest.mark.asyncio
async def test_collector_with_one_sink_multiple_data_points(mocker: MockerFixture, test_type: MeterDataPointType):
    coll = Collector()
    sink = mocker.AsyncMock(DataSink)

    coll.register_sink(sink)
    point0 = MeterDataPoint(test_type, 0.0, OBISCode(0, 1, 2, 3, 4, 5))
    point1 = MeterDataPoint(test_type, 1.0, OBISCode(0, 1, 3, 4, 5, 6))
    data_bundle = MeterDataBundle("test_source", datetime.now(timezone.utc), [point0, point1])
    coll.notify(data_bundle)
    routine = coll.process_queue()

    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(routine, 0.1)

    sink.send.assert_awaited_once_with(data_bundle)


@pytest.mark.asyncio
async def test_collector_with_two_sinks(mocker: MockerFixture, test_type: MeterDataPointType):
    coll = Collector()
    sink0 = mocker.AsyncMock(DataSink)
    sink1 = mocker.AsyncMock(DataSink)

    data_point = MeterDataPoint(test_type, 0.0, OBISCode(0, 1, 2, 3, 4, 5))
    data_bundle = MeterDataBundle("test_source", datetime.now(timezone.utc), [data_point])

    coll.register_sink(sink0)
    coll.register_sink(sink1)
    coll.notify(data_bundle)
    routine = coll.process_queue()

    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(routine, 0.1)

    sink0.send.assert_awaited_once_with(data_bundle)
    sink1.send.assert_awaited_once_with(data_bundle)
