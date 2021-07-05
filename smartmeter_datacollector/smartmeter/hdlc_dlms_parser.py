import logging
from typing import List, Tuple
from gurux_dlms import GXDLMSClient, GXDLMSTranslator
from gurux_dlms.GXByteBuffer import GXByteBuffer
from gurux_dlms.GXReplyData import GXReplyData
from gurux_dlms.objects.GXDLMSObject import GXDLMSObject
from gurux_dlms.objects.GXDLMSObjectCollection import GXDLMSObjectCollection

LOGGER = logging.getLogger("smartmeter")

class HdlcDlmsParser:
    def __init__(self) -> None:
        self._client = GXDLMSClient(True)
        self._hdlc_buffer = GXByteBuffer()
        self._dlms_data = GXReplyData()

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
            self._client.getData(self._hdlc_buffer, tmp, self._dlms_data)
        except ValueError as ex:
            LOGGER.debug("Unable to extract data from hdlc frame: '%s'", ex)
            self._hdlc_buffer.clear()
            self._dlms_data.clear()
            return False

        self._hdlc_buffer.clear()
        if not self._dlms_data.isComplete():
            LOGGER.debug("Incomplete HDLC frame. DLMS buffer is cleared.")
            self._dlms_data.clear()
            return False

        if not self._dlms_data.isMoreData():
            LOGGER.debug("DLMS packet complete and ready for parsing.")
            return True
        return False

    def parse_to_dlms_objects(self) -> List[GXDLMSObject]:
        parsed_objects: List[Tuple[GXDLMSObject, int]] = []
        if isinstance(self._dlms_data.value, list):
            parsed_objects = self._client.parsePushObjects(self._dlms_data.value[0])
            for index, (obj, attr_ind) in enumerate(parsed_objects):
                if index == 0:
                    # Skip first (meta-data) object
                    continue
                self._client.updateValue(obj, attr_ind, self._dlms_data.value[index])
                LOGGER.debug(str(obj.objectType) + " " + obj.logicalName + " " + str(attr_ind) + ": " + str(obj.getValues()[attr_ind - 1]))
        self._dlms_data.clear()
        return [obj for obj, _ in parsed_objects]
