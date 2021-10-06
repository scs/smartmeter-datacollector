#
# Copyright (C) 2021 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
import logging
from typing import Any, Dict, List, Optional, Tuple

from gurux_dlms import GXByteBuffer, GXDLMSClient, GXReplyData
from gurux_dlms.enums import InterfaceType, ObjectType, Security
from gurux_dlms.objects import GXDLMSData, GXDLMSObject, GXDLMSRegister
from gurux_dlms.secure import GXDLMSSecureClient

from .cosem import Cosem
from .meter_data import MeterDataPoint

LOGGER = logging.getLogger("smartmeter")


class HdlcDlmsParser:
    HDLC_BUFFER_MAX_SIZE = 5000

    def __init__(self, cosem_config: Cosem, block_cipher_key: str = None) -> None:
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
        except ValueError as ex:
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
        parsed_objects: List[Tuple[GXDLMSObject, int]] = []
        if isinstance(self._dlms_data.value, list):
            #pylint: disable=unsubscriptable-object
            parsed_objects = self._client.parsePushObjects(self._dlms_data.value[0])
            for index, (obj, attr_ind) in enumerate(parsed_objects):
                if index == 0:
                    # Skip first (meta-data) object
                    continue
                self._client.updateValue(obj, attr_ind, self._dlms_data.value[index])
                LOGGER.debug("%s %s %s: %s", obj.objectType, obj.logicalName, attr_ind, obj.getValues()[attr_ind - 1])
        self._dlms_data.clear()
        return {obj.getName(): obj for obj, _ in parsed_objects}

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

    @staticmethod
    def _extract_value_from_data_object(data_object: GXDLMSData) -> Optional[Any]:
        return data_object.getValues()[1]

    @staticmethod
    def _extract_register_value(register: GXDLMSRegister) -> Optional[Any]:
        return register.getValues()[1]
