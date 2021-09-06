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
class MeterDataPointType:
    identifier: str
    name: str
    unit: str


class MeterDataPointTypes(Enum):
    ACTIVE_POWER_P = MeterDataPointType("ACTIVE_POWER_P", "Active Power +", "W")
    ACTIVE_POWER_P_L1 = MeterDataPointType("ACTIVE_POWER_P_L1", "Active Power L1 +", "W")
    ACTIVE_POWER_P_L2 = MeterDataPointType("ACTIVE_POWER_P_L2", "Active Power L2 +", "W")
    ACTIVE_POWER_P_L3 = MeterDataPointType("ACTIVE_POWER_P_L3", "Active Power L3 +", "W")

    ACTIVE_POWER_N = MeterDataPointType("ACTIVE_POWER_N", "Active Power -", "W")
    ACTIVE_POWER_N_L1 = MeterDataPointType("ACTIVE_POWER_N_L1", "Active Power L1 -", "W")
    ACTIVE_POWER_N_L2 = MeterDataPointType("ACTIVE_POWER_N_L2", "Active Power L2 -", "W")
    ACTIVE_POWER_N_L3 = MeterDataPointType("ACTIVE_POWER_N_L3", "Active Power L3 -", "W")

    REACTIVE_POWER_P = MeterDataPointType("REACTIVE_POWER_P", "Reactive Power +", "VA")
    REACTIVE_POWER_P_L1 = MeterDataPointType("REACTIVE_POWER_P_L1", "Reactive Power L1 +", "VA")
    REACTIVE_POWER_P_L2 = MeterDataPointType("REACTIVE_POWER_P_L2", "Reactive Power L2 +", "VA")
    REACTIVE_POWER_P_L3 = MeterDataPointType("REACTIVE_POWER_P_L3", "Reactive Power L3 +", "VA")

    REACTIVE_POWER_N = MeterDataPointType("REACTIVE_POWER_N", "Reactive Power -", "VA")
    REACTIVE_POWER_N_L1 = MeterDataPointType("REACTIVE_POWER_N_L1", "Reactive Power L1 -", "VA")
    REACTIVE_POWER_N_L2 = MeterDataPointType("REACTIVE_POWER_N_L2", "Reactive Power L2 -", "VA")
    REACTIVE_POWER_N_L3 = MeterDataPointType("REACTIVE_POWER_N_L3", "Reactive Power L3 -", "VA")

    CURRENT_L1 = MeterDataPointType("CURRENT_L1", "Current L1", "A")
    CURRENT_L2 = MeterDataPointType("CURRENT_L2", "Current L2", "A")
    CURRENT_L3 = MeterDataPointType("CURRENT_L3", "Current L3", "A")

    VOLTAGE_L1 = MeterDataPointType("VOLTAGE_L1", "Voltage L1", "V")
    VOLTAGE_L2 = MeterDataPointType("VOLTAGE_L2", "Voltage L2", "V")
    VOLTAGE_L3 = MeterDataPointType("VOLTAGE_L3", "Voltage L3", "V")

    ANGLE_UI_L1 = MeterDataPointType("ANGLE_UI_L1", "Angle U-I L1", "rad")
    ANGLE_UI_L2 = MeterDataPointType("ANGLE_UI_L2", "Angle U-I L2", "rad")
    ANGLE_UI_L3 = MeterDataPointType("ANGLE_UI_L3", "Angle U-I L3", "rad")

    ACTIVE_ENERGY_P = MeterDataPointType("ACTIVE_ENERGY_P", "Active Energy +", "Wh")
    ACTIVE_ENERGY_N = MeterDataPointType("ACTIVE_ENERGY_N", "Active Energy -", "Wh")

    REACTIVE_ENERGY_P = MeterDataPointType("REACTIVE_ENERGY_P", "Reactive Energy +", "VAh")
    REACTIVE_ENERGY_N = MeterDataPointType("REACTIVE_ENERGY_N", "Reactive Energy -", "VAh")

    REACTIVE_ENERGY_Q1 = MeterDataPointType("REACTIVE_ENERGY_Q1", "Reactive Energy +Ri Q1", "VAh")
    REACTIVE_ENERGY_Q2 = MeterDataPointType("REACTIVE_ENERGY_Q2", "Reactive Energy +Rc Q2", "VAh")
    REACTIVE_ENERGY_Q3 = MeterDataPointType("REACTIVE_ENERGY_Q3", "Reactive Energy -Ri Q3", "VAh")
    REACTIVE_ENERGY_Q4 = MeterDataPointType("REACTIVE_ENERGY_Q4", "Reactive Energy -Rc Q4", "VAh")

    POWER_FACTOR = MeterDataPointType("POWER_FACTOR", "Power Factor", "")
    NET_FREQUENCY = MeterDataPointType("NET_FREQUENCY", "Net Frequency any Phase", "Hz")


@dataclass
class MeterDataPoint:
    type: MeterDataPointType
    value: float
    source: str
    timestamp: datetime

    def __str__(self) -> str:
        return f"{self.source} - {self.timestamp.isoformat()} - {self.type.name}: {self.value} {self.type.unit}"

    def to_json(self) -> str:
        dict_repr = dataclasses.asdict(self)
        dict_repr['timestamp'] = self.timestamp.isoformat()
        return json.dumps(dict_repr)
