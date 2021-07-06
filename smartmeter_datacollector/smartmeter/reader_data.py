from dataclasses import dataclass
from datetime import datetime
from enum import Enum


@dataclass
class ReaderDataPointType:
    name: str
    unit: str


class ReaderDataPointTypes(Enum):
    ACTIVE_POWER_P = ReaderDataPointType("Active Power +", "W")
    ACTIVE_POWER_N = ReaderDataPointType("Active Power -", "W")
    REACTIVE_POWER_P = ReaderDataPointType("Reactive Power +", "VA")
    REACTIVE_POWER_N = ReaderDataPointType("Reactive Power -", "VA")
    ACTIVE_POWER_P_INT = ReaderDataPointType("Active Power + Time Integral", "Wh")
    ACTIVE_POWER_N_INT = ReaderDataPointType("Active Power - Time Integral", "Wh")
    REACTIVE_POWER_Q1_INT = ReaderDataPointType("Reactive Power Q1 Time Integral", "VAh")
    REACTIVE_POWER_Q2_INT = ReaderDataPointType("Reactive Power Q2 Time Integral", "VAh")
    REACTIVE_POWER_Q3_INT = ReaderDataPointType("Reactive Power Q3 Time Integral", "VAh")
    REACTIVE_POWER_Q4_INT = ReaderDataPointType("Reactive Power Q4 Time Integral", "VAh")
    POWER_FACTOR = ReaderDataPointType("Power Factor", "")


@dataclass
class ReaderDataPoint:
    type: ReaderDataPointType
    value: float
    source: str
    ts: datetime
