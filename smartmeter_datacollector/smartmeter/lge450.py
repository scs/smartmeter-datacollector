import logging

import serial
from gurux_dlms import GXDLMSClient, GXDLMSTranslator
from gurux_dlms.GXByteBuffer import GXByteBuffer
from gurux_dlms.GXReplyData import GXReplyData

from .reader import Reader
from .serial_reader import SerialConfig, SerialReader

LOGGER = logging.getLogger("smartmeter")

class LGE450(Reader):
    def __init__(self, port: str) -> None:
        super().__init__()

        serial_config = SerialConfig(
            port=port,
            baudrate=2400,
            data_bits=serial.EIGHTBITS,
            parity=serial.PARITY_EVEN,
            stop_bits=serial.STOPBITS_ONE,
            termination=None
        )
        self._serial = SerialReader(serial_config, self._data_received)
        self._dlms = GXDLMSClient(True)
        self._receive_buffer = GXByteBuffer()
        self._notify = GXReplyData()
        self._translator = GXDLMSTranslator()

    async def start(self) -> None:
        await self._serial.start_and_listen()

    def _data_received(self, received_data: bytes) -> None:
        LOGGER.debug("Data received: %s", str(received_data))
        self._receive_buffer.set(received_data)
        data = GXReplyData()
        try:
            if not self._dlms.getData(self._receive_buffer, data, self._notify):
                if self._notify.complete:
                    if not self._notify.isMoreData():
                        xml = self._translator.dataToXml(self._notify.data)
                        LOGGER.debug("XML data: %s", str(xml))
                        if isinstance(self._notify.value, list):
                            objects = self._dlms.parsePushObjects(self._notify.value[0])
                            #Remove first item because it's not needed anymore.
                            objects.pop(0)
                            value_index = 1
                            for obj, index in objects:
                                self._dlms.updateValue(obj, index, self._notify.value[value_index])
                                value_index += 1
                                #Print value
                                print(str(obj.objectType) + " " + obj.logicalName + " " + str(index) + ": " + str(obj.getValues()[index - 1]))
                        self._notify.clear()
                        self._receive_buffer.clear()
        except Exception as e:
            LOGGER.error("Failed to get and parse data: '%s'", e)
            raise e

    @classmethod
    def print_value(cls, value, offset):
        sb = ' ' * 2 * offset
        if isinstance(value, list):
            print(sb + "{")
            offset = offset + 1
            #Print received data.
            for it in value:
                cls.print_value(it, offset)
            print(sb + "}")
            offset = offset - 1
        elif isinstance(value, bytearray):
            #Print value.
            print(sb + value.hex())
        else:
            #Print value.
            print(sb + str(value))
