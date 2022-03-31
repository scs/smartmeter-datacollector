#
# Copyright (C) 2022 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
import json
from datetime import datetime

from smartmeter_datacollector.smartmeter.meter_data import MeterDataPoint, MeterDataPointType


def test_meter_data_serialize():
    test_type = MeterDataPointType("TEST_TYPE", "test type", "unit")
    data_point = MeterDataPoint(test_type, 1.0, "TestSource", datetime.utcnow())

    data_point_json = data_point.to_json()

    result = json.loads(data_point_json)
    assert result['type']['identifier'] == data_point.type.identifier
    assert result['type']['name'] == data_point.type.name
    assert result['type']['unit'] == data_point.type.unit
    assert result['value'] == data_point.value
    assert result['source'] == data_point.source
    assert result['timestamp'] == data_point.timestamp.isoformat()
