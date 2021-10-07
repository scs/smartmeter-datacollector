#
# Copyright (C) 2021 Supercomputing Systems AG
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

from .meter_data import MeterDataPointType

LOGGER = logging.getLogger("smartmeter")

OBIS_DEFAULT_IDS = [
    "0.0.42.0.0.255",
    "0.0.96.1.0.255",
    "0.0.96.2.0.255",
    "0.0.96.3.0.255",
    "0.0.96.4.0.255",
    "0.0.96.5.0.255"
]
OBIS_DEFAULT_CLOCK = "0.0.1.0.0.255"
COSEM_OBJECT_DETECT_ATTEMPTS = 3


@dataclass
class RegisterCosem:
    obis: str
    data_point_type: MeterDataPointType
    scaling: float = 1.0


class Cosem:
    def __init__(self, fallback_id: str, register_obis: List[RegisterCosem]) -> None:
        self._id: Optional[str] = None
        if not fallback_id:
            fallback_id = str(uuid.uuid1())
            LOGGER.warning("Empty or no fallback ID. Setting to random UUID %s.", fallback_id)
        self._fallback_id = fallback_id
        self._register_obis = {r.obis: r for r in register_obis}
        self._id_detect_countdown = COSEM_OBJECT_DETECT_ATTEMPTS

    def retrieve_id(self, dlms_objects: Dict[str, Any]) -> str:
        if self._id:
            return self._id

        id_obis = self._find_id_obis(dlms_objects)
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

    def retrieve_timestamp(self, dlms_objects: Dict[str, Any]) -> datetime:
        clock_obj = dlms_objects.get(OBIS_DEFAULT_CLOCK, None)
        if clock_obj and isinstance(clock_obj, GXDLMSClock):
            timestamp = self._extract_datetime(clock_obj)
            if timestamp:
                return timestamp

            LOGGER.warning("Unable to parse timestamp from %s. Using system time.", OBIS_DEFAULT_CLOCK)
        else:
            LOGGER.debug("No clock object found at %s. Using system time.", OBIS_DEFAULT_CLOCK)

        return datetime.utcnow()

    def get_register(self, obis: str) -> Optional[RegisterCosem]:
        return self._register_obis.get(obis, None)

    def _trigger_id_detect_counter(self):
        self._id_detect_countdown -= 1
        if self._id_detect_countdown <= 0:
            LOGGER.warning("Unable to retrieve ID after %i attempts. Using fallback ID %s from now on.",
                           COSEM_OBJECT_DETECT_ATTEMPTS, self._fallback_id)
            self._id = self._fallback_id

    @staticmethod
    def _find_id_obis(dlms_objects: Dict[str, Any]) -> Optional[str]:
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
