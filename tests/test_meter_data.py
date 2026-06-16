#
# Copyright (C) 2024 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
import json
from datetime import datetime, timezone

from smartmeter_datacollector.smartmeter.meter_data import MeterDataBundle, MeterDataPoint, MeterDataPointType
from smartmeter_datacollector.smartmeter.obis import OBISCode


def test_meter_data_serialize():
    test_type = MeterDataPointType("TEST_TYPE", "test type", "unit")
    obis_test = OBISCode(0, 1, 2, 3, 4, 5)
    timestamp = datetime.now(timezone.utc)
    data_point = MeterDataPoint(test_type, 1.0, obis_test)
    data_bundle = MeterDataBundle("TestSource", timestamp, [data_point])

    data_point_json = data_point.to_json(short_obis=False)
    data_bundle_json = data_bundle.to_json(short_obis=False)

    result = json.loads(data_point_json)
    assert result['type']['identifier'] == data_point.type.identifier
    assert result['type']['name'] == data_point.type.name
    assert result['type']['unit'] == data_point.type.unit
    assert result['value'] == data_point.value
    assert result['obis'] == str(obis_test)

    bundle_result = json.loads(data_bundle_json)
    assert bundle_result['source'] == data_bundle.source
    assert bundle_result['timestamp'] == data_bundle.timestamp.isoformat()
    assert len(bundle_result['data_points']) == 1


def test_meter_data_serialize_short_obis():
    test_type = MeterDataPointType("TEST_TYPE", "test type", "unit")
    obis_test = OBISCode(0, 1, 2, 3, 4, 5)
    data_point = MeterDataPoint(test_type, 1.0, obis_test)

    data_point_json_short_obis = data_point.to_json(short_obis=True)
    result = json.loads(data_point_json_short_obis)
    assert result['obis'] == obis_test.to_short_str()
