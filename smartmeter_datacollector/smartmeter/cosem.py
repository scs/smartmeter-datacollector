#
# Copyright (C) 2021 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
from dataclasses import dataclass
from typing import List, Optional

from .meter_data import MeterDataPointType


@dataclass
class RegisterCosem:
    obis: str
    data_point_type: MeterDataPointType
    scaling: float = 1.0


class CosemConfig:
    def __init__(self, id_obis: str, clock_obis: str, register_obis: List[RegisterCosem]) -> None:

        self._id_obis = id_obis
        self._clock_obis = clock_obis
        self._register_obis = {r.obis: r for r in register_obis}

    @property
    def id_obis(self) -> str:
        return self._id_obis

    @property
    def clock_obis(self) -> str:
        return self._clock_obis

    def get_register(self, obis: str) -> Optional[RegisterCosem]:
        return self._register_obis.get(obis, None)
