#
# Copyright (C) 2022 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
import logging
from typing import Any, Dict, List, Optional, Tuple

from gurux_dlms import GXByteBuffer, GXDLMSClient, GXReplyData
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

    def __init__(self, cosem_config: Cosem, block_cipher_key: Optional[str] = None) -> None:
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
        self._cosem = cosem_config

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

    def parse_to_dlms_objects(self) -> Dict[str, GXDLMSObject]:
        if not isinstance(self._dlms_data.value, list) or not self._dlms_data.value:
            self._dlms_data.clear()
            LOGGER.warning("DLMS data is no list or empty list. Not parsable.")
            return {}

        # pylint: disable=unsubscriptable-object
        if isinstance(self._dlms_data.value[0], list):
            # message with included push-object-list as first object
            dlms_objects = self._parse_dlms_with_push_object_list()
        else:
            # message without push-object-list
            # try to extract OBIS codes if available in message
            obis_codes = HdlcDlmsParser.extract_obis(self._dlms_data.value)
            if obis_codes:
                # message contains OBIS code/value pairs
                # message format supported: timestamp + OBIS code/value pairs
                push_setup = GXDLMSPushSetup()
                push_setup.pushObjectList.append((GXDLMSClock(), GXDLMSCaptureObject(2, 0)))
                push_setup.pushObjectList.extend((GXDLMSRegister(obis.to_gurux_str()), GXDLMSCaptureObject(2, 0))
                                                 for obis in obis_codes)

                values = HdlcDlmsParser.extract_values(self._dlms_data.value)
                if len(values) != len(obis_codes):
                    LOGGER.warning("Values list and OBIS code list length not equal.")

                for index, (obj, attr_ind) in enumerate(push_setup.pushObjectList):
                    self._client.updateValue(obj, attr_ind.attributeIndex, values[index])
                    LOGGER.debug("%d %s %s %s: %s", index, obj.objectType, obj.logicalName,
                                 attr_ind.attributeIndex, obj.getValues()[attr_ind.attributeIndex - 1])
                dlms_objects = {obj.getName(): obj for obj, _ in push_setup.pushObjectList}
            else:
                # message contains no OBIS codes, only values, which is not supported.
                LOGGER.warning("DLMS data is formatted in unknown structure and cannot be parsed.")
                dlms_objects = {}

        self._dlms_data.clear()
        return dlms_objects

    def convert_dlms_bundle_to_reader_data(self, dlms_objects: Dict[str, GXDLMSObject]) -> List[MeterDataPoint]:
        meter_id = self._cosem.retrieve_id(dlms_objects)
        timestamp = self._cosem.retrieve_timestamp(dlms_objects)

        # Extract register data
        data_points: List[MeterDataPoint] = []
        for obis, obj in filter(lambda o: o[1].getObjectType() == ObjectType.REGISTER, dlms_objects.items()):
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

    def _parse_dlms_with_push_object_list(self) -> Dict[str, GXDLMSObject]:
        parsed_objects: List[Tuple[GXDLMSObject, int]] = []
        parsed_objects = self._client.parsePushObjects(self._dlms_data.value[0])
        for index, (obj, attr_ind) in enumerate(parsed_objects[1:], start=1):
            self._client.updateValue(obj, attr_ind, self._dlms_data.value[index])
            LOGGER.debug("%s %s %s: %s", obj.objectType, obj.logicalName, attr_ind, obj.getValues()[attr_ind - 1])
        return {obj.getName(): obj for obj, _ in parsed_objects}

    @staticmethod
    def _extract_value_from_data_object(data_object: GXDLMSData) -> Optional[Any]:
        return data_object.getValues()[1]

    @staticmethod
    def _extract_register_value(register: GXDLMSRegister) -> Optional[Any]:
        return register.getValues()[1]

    @staticmethod
    def extract_obis(data: List[Any]) -> List[OBISCode]:
        extracted_obis = []
        for obis_bytes in filter(lambda d: isinstance(d, (bytearray, bytes)), data):
            obis = OBISCode.from_bytes(obis_bytes)
            if obis:
                extracted_obis.append(obis)
        return extracted_obis

    @staticmethod
    def extract_values(data: List[Any]) -> List[Any]:
        return list(filter(
            lambda d: isinstance(d, int) or (isinstance(d, (bytes, bytearray)) and not OBISCode.is_obis(d)),
            data))
