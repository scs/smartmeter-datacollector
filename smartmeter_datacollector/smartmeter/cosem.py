#
# Copyright (C) 2022 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from gurux_dlms import GXDateTime
from gurux_dlms.objects import GXDLMSClock, GXDLMSData

from .meter_data import MeterDataPointType, MeterDataPointTypes
from .obis import OBISCode

LOGGER = logging.getLogger("smartmeter")


@dataclass
class RegisterCosem:
    obis: OBISCode
    data_point_type: MeterDataPointType
    scaling: float = 1.0


OBIS_DEFAULT_IDS = [
    OBISCode(0, 0, 42, 0, 0),
    OBISCode(0, 0, 96, 1, 0),
    OBISCode(0, 0, 96, 1, 1),
    OBISCode(0, 0, 96, 1, 2),
    OBISCode(0, 0, 96, 1, 3),
    OBISCode(0, 0, 96, 1, 4),
    OBISCode(0, 0, 96, 1, 5)
]
OBIS_DEFAULT_CLOCK = OBISCode(0, 0, 1, 0, 0)
COSEM_OBJECT_DETECT_ATTEMPTS = 3


DEFAULT_COSEM_REGISTERS = [
    RegisterCosem(OBISCode(1, 0, 1, 7, 0), MeterDataPointTypes.ACTIVE_POWER_P.value),
    RegisterCosem(OBISCode(1, 0, 2, 7, 0), MeterDataPointTypes.ACTIVE_POWER_N.value),
    RegisterCosem(OBISCode(1, 0, 3, 7, 0), MeterDataPointTypes.REACTIVE_POWER_P.value),
    RegisterCosem(OBISCode(1, 0, 4, 7, 0), MeterDataPointTypes.REACTIVE_POWER_N.value),

    RegisterCosem(OBISCode(1, 0, 13, 7, 0), MeterDataPointTypes.POWER_FACTOR.value, 0.001),
    RegisterCosem(OBISCode(1, 0, 14, 7, 0), MeterDataPointTypes.NET_FREQUENCY.value),

    RegisterCosem(OBISCode(1, 0, 21, 7, 0), MeterDataPointTypes.ACTIVE_POWER_P_L1.value),
    RegisterCosem(OBISCode(1, 0, 22, 7, 0), MeterDataPointTypes.ACTIVE_POWER_N_L1.value),
    RegisterCosem(OBISCode(1, 0, 23, 7, 0), MeterDataPointTypes.REACTIVE_POWER_P_L1.value),
    RegisterCosem(OBISCode(1, 0, 24, 7, 0), MeterDataPointTypes.REACTIVE_POWER_N_L1.value),

    RegisterCosem(OBISCode(1, 0, 31, 7, 0), MeterDataPointTypes.CURRENT_L1.value),
    RegisterCosem(OBISCode(1, 0, 32, 7, 0), MeterDataPointTypes.VOLTAGE_L1.value),

    RegisterCosem(OBISCode(1, 0, 41, 7, 0), MeterDataPointTypes.ACTIVE_POWER_P_L2.value),
    RegisterCosem(OBISCode(1, 0, 42, 7, 0), MeterDataPointTypes.ACTIVE_POWER_N_L2.value),
    RegisterCosem(OBISCode(1, 0, 43, 7, 0), MeterDataPointTypes.REACTIVE_POWER_P_L2.value),
    RegisterCosem(OBISCode(1, 0, 44, 7, 0), MeterDataPointTypes.REACTIVE_POWER_N_L2.value),

    RegisterCosem(OBISCode(1, 0, 51, 7, 0), MeterDataPointTypes.CURRENT_L2.value),
    RegisterCosem(OBISCode(1, 0, 52, 7, 0), MeterDataPointTypes.VOLTAGE_L2.value),

    RegisterCosem(OBISCode(1, 0, 61, 7, 0), MeterDataPointTypes.ACTIVE_POWER_P_L3.value),
    RegisterCosem(OBISCode(1, 0, 62, 7, 0), MeterDataPointTypes.ACTIVE_POWER_N_L3.value),
    RegisterCosem(OBISCode(1, 0, 63, 7, 0), MeterDataPointTypes.REACTIVE_POWER_P_L3.value),
    RegisterCosem(OBISCode(1, 0, 64, 7, 0), MeterDataPointTypes.REACTIVE_POWER_N_L3.value),

    RegisterCosem(OBISCode(1, 0, 71, 7, 0), MeterDataPointTypes.CURRENT_L3.value),
    RegisterCosem(OBISCode(1, 0, 72, 7, 0), MeterDataPointTypes.VOLTAGE_L3.value),

    RegisterCosem(OBISCode(1, 0, 81, 7, 40), MeterDataPointTypes.ANGLE_UI_L1.value),
    RegisterCosem(OBISCode(1, 0, 81, 7, 51), MeterDataPointTypes.ANGLE_UI_L2.value),
    RegisterCosem(OBISCode(1, 0, 81, 7, 62), MeterDataPointTypes.ANGLE_UI_L3.value),

    RegisterCosem(OBISCode(1, 0, 1, 8, 0), MeterDataPointTypes.ACTIVE_ENERGY_P.value),
    RegisterCosem(OBISCode(1, 0, 1, 8, 1), MeterDataPointTypes.ACTIVE_ENERGY_P_T1.value),
    RegisterCosem(OBISCode(1, 0, 1, 8, 2), MeterDataPointTypes.ACTIVE_ENERGY_P_T2.value),
    RegisterCosem(OBISCode(1, 0, 2, 8, 0), MeterDataPointTypes.ACTIVE_ENERGY_N.value),
    RegisterCosem(OBISCode(1, 0, 2, 8, 1), MeterDataPointTypes.ACTIVE_ENERGY_N_T1.value),
    RegisterCosem(OBISCode(1, 0, 2, 8, 2), MeterDataPointTypes.ACTIVE_ENERGY_N_T2.value),
    RegisterCosem(OBISCode(1, 0, 3, 8, 0), MeterDataPointTypes.REACTIVE_ENERGY_P.value),
    RegisterCosem(OBISCode(1, 0, 3, 8, 1), MeterDataPointTypes.REACTIVE_ENERGY_P_T1.value),
    RegisterCosem(OBISCode(1, 0, 3, 8, 2), MeterDataPointTypes.REACTIVE_ENERGY_P_T2.value),
    RegisterCosem(OBISCode(1, 0, 4, 8, 0), MeterDataPointTypes.REACTIVE_ENERGY_N.value),
    RegisterCosem(OBISCode(1, 0, 4, 8, 1), MeterDataPointTypes.REACTIVE_ENERGY_N_T1.value),
    RegisterCosem(OBISCode(1, 0, 4, 8, 2), MeterDataPointTypes.REACTIVE_ENERGY_N_T2.value),

    RegisterCosem(OBISCode(1, 0, 5, 8, 0), MeterDataPointTypes.REACTIVE_ENERGY_Q1.value),
    RegisterCosem(OBISCode(1, 0, 6, 8, 0), MeterDataPointTypes.REACTIVE_ENERGY_Q2.value),
    RegisterCosem(OBISCode(1, 0, 7, 8, 0), MeterDataPointTypes.REACTIVE_ENERGY_Q3.value),
    RegisterCosem(OBISCode(1, 0, 8, 8, 0), MeterDataPointTypes.REACTIVE_ENERGY_Q4.value),
]


class Cosem:
    def __init__(self, fallback_id: str, register_obis: List[RegisterCosem] = DEFAULT_COSEM_REGISTERS) -> None:
        self._id: Optional[str] = None
        if not fallback_id:
            fallback_id = str(uuid.uuid1())
            LOGGER.warning("Empty or no fallback ID. Setting to random UUID %s.", fallback_id)
        self._fallback_id = fallback_id
        self._register_obis = {r.obis: r for r in register_obis}
        self._id_detect_countdown = COSEM_OBJECT_DETECT_ATTEMPTS

    def retrieve_id(self, dlms_objects: Dict[OBISCode, Any]) -> str:
        if self._id:
            return self._id

        id_obis = self._find_obis_of_id(dlms_objects)
        if not id_obis:
            LOGGER.debug("Unable to find ID object. Using fallback ID %s.", self._fallback_id)
            self._trigger_id_detect_counter()
            return self._fallback_id

        id_obj = dlms_objects[id_obis]
        if not isinstance(id_obj, GXDLMSData):
            LOGGER.debug("Invalid ID object for OBIS code %s. Using fallback ID %s.", id_obis, self._fallback_id)
            self._trigger_id_detect_counter()
            return self._fallback_id

        meter_id = id_obj.getValues()[1]
        if not isinstance(meter_id, str) or len(meter_id) == 0:
            LOGGER.debug("Invalid ID for OBIS code %s. Using fallback ID %s.", id_obis, self._fallback_id)
            self._trigger_id_detect_counter()
            return self._fallback_id

        self._id = meter_id
        LOGGER.debug("ID %s found with OBIS code %s.", meter_id, id_obis)
        return meter_id

    def retrieve_timestamp(self, dlms_objects: Dict[OBISCode, Any]) -> datetime:
        clock_obj = dlms_objects.get(OBIS_DEFAULT_CLOCK, None)
        if clock_obj and isinstance(clock_obj, GXDLMSClock):
            timestamp = self._extract_datetime(clock_obj)
            if timestamp:
                return timestamp

            LOGGER.warning("Unable to parse timestamp from %s. Using system time.", str(OBIS_DEFAULT_CLOCK))
        else:
            LOGGER.debug("No clock object found at %s. Using system time.", str(OBIS_DEFAULT_CLOCK))

        return datetime.utcnow()

    def get_register(self, obis: OBISCode) -> Optional[RegisterCosem]:
        return self._register_obis.get(obis, None)

    def _trigger_id_detect_counter(self):
        self._id_detect_countdown -= 1
        if self._id_detect_countdown <= 0:
            LOGGER.warning("Unable to retrieve ID after %i attempts. Using fallback ID %s from now on.",
                           COSEM_OBJECT_DETECT_ATTEMPTS, self._fallback_id)
            self._id = self._fallback_id

    @staticmethod
    def _find_obis_of_id(dlms_objects: Dict[OBISCode, Any]) -> Optional[OBISCode]:
        for default_obis in OBIS_DEFAULT_IDS:
            if default_obis in dlms_objects:
                return default_obis
        return None

    @staticmethod
    def _extract_datetime(clock_object: GXDLMSClock) -> Optional[datetime]:
        time_obj: GXDateTime = clock_object.getValues()[1]
        if isinstance(time_obj, GXDateTime):
            return time_obj.value
        return None
