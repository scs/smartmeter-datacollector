#
# Copyright (C) 2022 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
import logging
from datetime import datetime
from typing import Any, List, Optional, Tuple

from gurux_dlms import GXByteBuffer, GXDateTime, GXDLMSClient, GXReplyData
from gurux_dlms.enums import InterfaceType, ObjectType, Security
from gurux_dlms.objects import (GXDLMSCaptureObject, GXDLMSClock, GXDLMSData, GXDLMSObject, GXDLMSPushSetup,
                                GXDLMSRegister)
from gurux_dlms.secure import GXDLMSSecureClient

from .cosem import Cosem
from .meter_data import MeterDataPoint
from .obis import OBISCode

LOGGER = logging.getLogger("smartmeter")


class HdlcDlmsParser:
    HDLC_BUFFER_MAX_SIZE = 5000

    def __init__(self, cosem: Cosem, block_cipher_key: Optional[str] = None, use_system_time: bool = False) -> None:
        if block_cipher_key:
            self._client = GXDLMSSecureClient(
                useLogicalNameReferencing=True,
                interfaceType=InterfaceType.HDLC)
            self._client.ciphering.security = Security.ENCRYPTION
            self._client.ciphering.blockCipherKey = GXByteBuffer.hexToBytes(block_cipher_key)
        else:
            self._client = GXDLMSClient(
                useLogicalNameReferencing=True,
                interfaceType=InterfaceType.HDLC)

        self._hdlc_buffer = GXByteBuffer()
        self._dlms_data = GXReplyData()
        self._cosem = cosem
        self._use_system_time = use_system_time
        if use_system_time:
            LOGGER.info("Use system UTC time instead of time in DLMS messages for this smart meter.")

    def append_to_hdlc_buffer(self, data: bytes) -> None:
        if self._hdlc_buffer.getSize() > self.HDLC_BUFFER_MAX_SIZE:
            LOGGER.warning("HDLC byte-buffer > %i. Buffer is cleared, some data is lost.",
                           self.HDLC_BUFFER_MAX_SIZE)
            self._hdlc_buffer.clear()
            self._dlms_data.clear()
        self._hdlc_buffer.set(data)

    def clear_hdlc_buffer(self) -> None:
        self._hdlc_buffer.clear()

    def extract_data_from_hdlc_frames(self) -> bool:
        """
        Try to extract data fragments from HDLC frame-buffer and store it into DLMS buffer.
        HDLC buffer is being cleared.
        Returns: True if data is complete for parsing.
        """
        tmp = GXReplyData()
        try:
            LOGGER.debug("HDLC Buffer: %s", GXByteBuffer.hex(self._hdlc_buffer))
            self._client.getData(self._hdlc_buffer, tmp, self._dlms_data)
        except (ValueError, TypeError) as ex:
            LOGGER.warning("Failed to extract data from HDLC frame: '%s' Some data got lost.", ex)
            self._hdlc_buffer.clear()
            self._dlms_data.clear()
            return False

        if not self._dlms_data.isComplete():
            LOGGER.debug("HDLC frame incomplete and will not be parsed yet.")
            return False

        if self._dlms_data.isMoreData():
            LOGGER.debug("More DLMS data expected. Not yet ready to be parsed.")
            return False

        LOGGER.debug("DLMS packet complete and ready for parsing.")
        self._hdlc_buffer.clear()
        return True

    def extract_message_time(self) -> Optional[datetime]:
        if not isinstance(self._dlms_data.time, GXDateTime):
            return None
        if isinstance(self._dlms_data.time.value, datetime):
            return self._dlms_data.time.value
        return None

    def parse_to_dlms_objects(self) -> List[GXDLMSObject]:
        if not isinstance(self._dlms_data.value, list) or not self._dlms_data.value:
            self._dlms_data.clear()
            LOGGER.error("DLMS data is no list or empty list. Not parsable.")
            return []

        # pylint: disable=unsubscriptable-object
        if isinstance(self._dlms_data.value[0], list):
            # message with included push-object-list as first object
            dlms_objects = self._parse_dlms_with_push_object_list()
        else:
            # message without push-object-list
            dlms_objects = self._parse_dlms_without_push_list()
            if not dlms_objects:
                # message contains no OBIS codes, only values, which is not supported.
                LOGGER.warning("DLMS message is formatted in unknown structure and cannot be parsed by this software.")
        self._dlms_data.clear()
        return dlms_objects

    def convert_dlms_bundle_to_reader_data(self, dlms_objects: List[GXDLMSObject],
                                           message_time: Optional[datetime] = None) -> List[MeterDataPoint]:
        obis_obj_pairs = {}
        for obj in dlms_objects:
            try:
                obis_obj_pairs[OBISCode.from_string(str(obj.logicalName))] = obj
            except ValueError as ex:
                LOGGER.warning("Skipping unparsable DLMS object. (Reason: %s)", ex)

        meter_id = self._cosem.retrieve_id(obis_obj_pairs)

        timestamp = None
        if self._use_system_time:
            timestamp = datetime.utcnow()

        if not timestamp:
            timestamp = self._cosem.retrieve_time_from_dlms_registers(obis_obj_pairs)
        if not timestamp:
            timestamp = message_time
        if not timestamp:
            LOGGER.warning("Unable to get timestamp from message. Falling back to system time.")
            self._use_system_time = True
            timestamp = datetime.utcnow()

        # Extract register data
        data_points: List[MeterDataPoint] = []
        for obis, obj in filter(lambda o: o[1].getObjectType() == ObjectType.REGISTER, obis_obj_pairs.items()):
            reg_type = self._cosem.get_register(obis)
            if reg_type and isinstance(obj, GXDLMSRegister):
                raw_value = self._extract_register_value(obj)
                if raw_value is None:
                    LOGGER.warning("No value received for %s.", obis)
                    continue
                data_point_type = reg_type.data_point_type
                try:
                    value = float(raw_value) * reg_type.scaling
                except (TypeError, ValueError, OverflowError):
                    LOGGER.warning("Invalid register value '%s'. Skipping register.", str(raw_value))
                    continue
                data_points.append(MeterDataPoint(data_point_type, value, meter_id, timestamp))
        return data_points

    def _parse_dlms_with_push_object_list(self) -> List[GXDLMSObject]:
        parsed_objects: List[Tuple[GXDLMSObject, int]] = []
        parsed_objects = self._client.parsePushObjects(self._dlms_data.value[0])
        for index, (obj, attr_ind) in enumerate(parsed_objects[1:], start=1):
            self._client.updateValue(obj, attr_ind, self._dlms_data.value[index])
            LOGGER.debug("%s %s %s: %s", obj.objectType, obj.logicalName, attr_ind, obj.getValues()[attr_ind - 1])

        return [obj for obj, _ in parsed_objects]

    def _parse_dlms_without_push_list(self) -> List[GXDLMSObject]:
        """Tries to extract OBIS codes and values from message.
        Supported message format:
            - timestamp
            - obis code 1
            - value 1
            - obis code 2
            - value 2
            - ...
        """
        obis_codes, values = HdlcDlmsParser.extract_obis_and_values(self._dlms_data.value)
        if not obis_codes:
            return []

        push_setup = GXDLMSPushSetup()
        for obis in obis_codes:
            if obis == Cosem.CLOCK_DEFAULT_OBIS:
                push_setup.pushObjectList.append((GXDLMSClock(), GXDLMSCaptureObject(2, 0)))
            else:
                push_setup.pushObjectList.append((GXDLMSRegister(obis.to_gurux_str()), GXDLMSCaptureObject(2, 0)))

        for index, (obj, attr_ind) in enumerate(push_setup.pushObjectList):
            self._client.updateValue(obj, attr_ind.attributeIndex, values[index])
            LOGGER.debug("%d %s %s %s: %s", index, obj.objectType, obj.logicalName,
                         attr_ind.attributeIndex, obj.getValues()[attr_ind.attributeIndex - 1])
        return [obj for obj, _ in push_setup.pushObjectList]

    @staticmethod
    def _extract_value_from_data_object(data_object: GXDLMSData) -> Optional[Any]:
        return data_object.getValues()[1]

    @staticmethod
    def _extract_register_value(register: GXDLMSRegister) -> Optional[Any]:
        return register.getValues()[1]

    @staticmethod
    def extract_obis_and_values(data: List[Any]) -> Tuple[List[OBISCode], List[Any]]:
        obis_it = filter(lambda d: isinstance(d[1], (bytearray, bytes)) and OBISCode.is_obis(d[1]), enumerate(data))

        obis_codes = []
        values = []

        for idx, obis_bytes in obis_it:
            if idx + 1 < len(data) and HdlcDlmsParser.is_value(data[idx + 1]):
                obis_codes.append(OBISCode.from_bytes(obis_bytes))
                values.append(data[idx + 1])
            else:
                LOGGER.debug("Skipped OBIS code without subsequent value.")

        return obis_codes, values

    @staticmethod
    def is_value(data: Any) -> bool:
        return (
            isinstance(data, (int, str)) or
            (isinstance(data, (bytearray, bytes)) and not OBISCode.is_obis(data)))
