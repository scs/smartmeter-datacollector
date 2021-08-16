#
# Copyright (C) 2021 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
import dataclasses
import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


@dataclass
class ReaderDataPointType:
    identifier: str
    name: str
    unit: str


class ReaderDataPointTypes(Enum):
    ACTIVE_POWER_P = ReaderDataPointType("ACTIVE_POWER_P", "Active Power +", "W")
    ACTIVE_POWER_N = ReaderDataPointType("ACTIVE_POWER_N", "Active Power -", "W")
    REACTIVE_POWER_P = ReaderDataPointType("REACTIVE_POWER_P", "Reactive Power +", "VA")
    REACTIVE_POWER_N = ReaderDataPointType("REACTIVE_POWER_N", "Reactive Power -", "VA")
    ACTIVE_POWER_P_INT = ReaderDataPointType("ACTIVE_POWER_P_INT", "Active Power + Time Integral", "Wh")
    ACTIVE_POWER_N_INT = ReaderDataPointType("ACTIVE_POWER_N_INT", "Active Power - Time Integral", "Wh")
    REACTIVE_POWER_Q1_INT = ReaderDataPointType("REACTIVE_POWER_Q1_INT", "Reactive Power Q1 Time Integral", "VAh")
    REACTIVE_POWER_Q2_INT = ReaderDataPointType("REACTIVE_POWER_Q2_INT", "Reactive Power Q2 Time Integral", "VAh")
    REACTIVE_POWER_Q3_INT = ReaderDataPointType("REACTIVE_POWER_Q3_INT", "Reactive Power Q3 Time Integral", "VAh")
    REACTIVE_POWER_Q4_INT = ReaderDataPointType("REACTIVE_POWER_Q4_INT", "Reactive Power Q4 Time Integral", "VAh")
    POWER_FACTOR = ReaderDataPointType("POWER_FACTOR", "Power Factor", "")


@dataclass
class ReaderDataPoint:
    type: ReaderDataPointType
    value: float
    source: str
    timestamp: datetime

    def __str__(self) -> str:
        return f"{self.source} - {self.timestamp.isoformat()} - {self.type.name}: {self.value} {self.type.unit}"

    def to_json(self) -> str:
        dict_repr = dataclasses.asdict(self)
        dict_repr['timestamp'] = self.timestamp.isoformat()
        return json.dumps(dict_repr)
