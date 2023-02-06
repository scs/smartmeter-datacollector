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
import time
import asyncio

import pytest
from pytest_mock.plugin import MockerFixture

from smartmeter_datacollector.sinks.csv_sink import CsvSink
from smartmeter_datacollector.smartmeter.meter_data import MeterDataPoint, MeterDataPointType
from smartmeter_datacollector.smartmeter.lge450 import LGE450_COSEM_REGISTERS

TEST_TYPE = MeterDataPointType("TEST_TYPE", "test type", "unit")

@pytest.mark.skipif(sys.version_info < (3, 8), reason="Python3.7 does not support AsyncMock.")
@pytest.mark.asyncio
async def test_csv_sink_send_point():

    cfg_parser = configparser.ConfigParser()
    cfg_parser.read_dict({
        "sink0": {
            'type': "csv",
            'directory': "path_to_csv_files",
                },
        "reader0": {
            "type": "lge450"
        }
    })

    sink = CsvSink(cfg_parser, "sink0")

    await sink.send(MeterDataPoint(LGE450_COSEM_REGISTERS[0].data_point_type, 0.000, "bef test_source", datetime.utcnow()))
    await sink.send(MeterDataPoint(LGE450_COSEM_REGISTERS[1].data_point_type, 1.001, "bef test_source", datetime.utcnow()))

    await sink.start()

    await sink.send(MeterDataPoint(LGE450_COSEM_REGISTERS[2].data_point_type, 12.002, "test_source", datetime.utcnow()))
    await sink.send(MeterDataPoint(LGE450_COSEM_REGISTERS[3].data_point_type, 13.003, "test_source", datetime.utcnow()))
    await sink.send(MeterDataPoint(LGE450_COSEM_REGISTERS[10].data_point_type, 14.000, "test_source", datetime.utcnow()))

    await asyncio.sleep(1.5)
    await sink.stop()

    assert(True)
