import logging
from datetime import datetime
from typing import Any, Dict, List, Tuple, Union

from gurux_dlms import GXByteBuffer, GXDateTime, GXDLMSClient, GXReplyData
from gurux_dlms.enums import ObjectType
from gurux_dlms.objects import (GXDLMSClock, GXDLMSData, GXDLMSObject,
                                GXDLMSRegister)

from .cosem import CosemConfig
from .reader_data import ReaderDataPoint

LOGGER = logging.getLogger("smartmeter")


class HdlcDlmsParser:
    def __init__(self, cosem_config: CosemConfig) -> None:
        self._client = GXDLMSClient(True)
        # self._client.settings.standard = Standard.IDIS use IDIS for ISKRA meter?
        self._hdlc_buffer = GXByteBuffer()
        self._dlms_data = GXReplyData()
        self._cosem = cosem_config
        self._meter_id: str = "unknown"

    def append_to_hdlc_buffer(self, data: bytes) -> None:
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
            LOGGER.debug("Unable to extract data from hdlc frame: '%s'", ex)
            self._hdlc_buffer.clear()
            self._dlms_data.clear()
            return False

        if not self._dlms_data.isComplete():
            LOGGER.debug("Incomplete HDLC frame.")
            return False

        if not self._dlms_data.isMoreData():
            LOGGER.debug("DLMS packet complete and ready for parsing.")
            LOGGER.debug("DLMS Buffer: %s", GXByteBuffer.hex(self._dlms_data.data))
            self._hdlc_buffer.clear()
            return True
        return False

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
                LOGGER.debug(str(obj.objectType) + " " + obj.logicalName + " " +
                             str(attr_ind) + ": " + str(obj.getValues()[attr_ind - 1]))
        self._dlms_data.clear()
        return {obj.getName(): obj for obj, _ in parsed_objects}

    def convert_dlms_bundle_to_reader_data(self, dlms_objects: Dict[str, GXDLMSObject]) -> List[ReaderDataPoint]:
        clock_obj = dlms_objects.get(self._cosem.clock_obis, None)
        ts = None
        if clock_obj:
            ts = self._extract_datetime(clock_obj)

        if ts is None:
            LOGGER.warning("No timestamp available. Using SW UTC timestamp.")
            ts = datetime.utcnow()

        id_obj = dlms_objects.get(self._cosem.id_obis, None)
        id = None
        if id_obj:
            id = self._extract_value_from_data_object(id_obj)
        if isinstance(id, str) and len(id) > 0:
            self._meter_id = id

        data_points: List[ReaderDataPoint] = []
        for obis, obj in filter(lambda o: o[1].getObjectType() == ObjectType.REGISTER, dlms_objects.items()):
            reg_type = self._cosem.get_register(obis)
            if reg_type:
                raw_value = self._extract_register_value(obj)
                if raw_value is None:
                    LOGGER.warning("No value received for %s.", obis)
                    continue
                type = reg_type.data_point_type
                value = float(raw_value) * reg_type.scaling
                data_points.append(ReaderDataPoint(type, value, self._meter_id, ts))
        return data_points

    @staticmethod
    def _extract_datetime(clock_object: GXDLMSClock) -> Union[datetime, None]:
        assert isinstance(clock_object, GXDLMSClock)
        time_obj: GXDateTime = clock_object.getValues()[1]
        if isinstance(time_obj, GXDateTime):
            return time_obj.value
        return None

    @staticmethod
    def _extract_value_from_data_object(data_object: GXDLMSData) -> Union[Any, None]:
        assert isinstance(data_object, GXDLMSData)
        return data_object.getValues()[1]

    @staticmethod
    def _extract_register_value(register: GXDLMSRegister) -> Union[Any, None]:
        assert isinstance(register, GXDLMSRegister)
        return register.getValues()[1]
