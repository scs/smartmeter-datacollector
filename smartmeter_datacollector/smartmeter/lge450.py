import logging

import serial
from gurux_dlms.GXByteBuffer import GXByteBuffer

from .hdlc_dlms_parser import HdlcDlmsParser
from .reader import Reader
from .serial_reader import SerialConfig, SerialReader

LOGGER = logging.getLogger("smartmeter")

class LGE450(Reader):
    HDLC_FLAG = b"\x7e"
    def __init__(self, port: str) -> None:
        super().__init__()

        serial_config = SerialConfig(
            port=port,
            baudrate=2400,
            data_bits=serial.EIGHTBITS,
            parity=serial.PARITY_EVEN,
            stop_bits=serial.STOPBITS_ONE,
            termination=LGE450.HDLC_FLAG
        )
        self._serial = SerialReader(serial_config, self._data_received)
        self._parser = HdlcDlmsParser()
        

    async def start(self) -> None:
        await self._serial.start_and_listen()

    def _data_received(self, received_data: bytes) -> None:
        if not received_data:
            return
        if received_data == LGE450.HDLC_FLAG:
            self._parser.append_to_hdlc_buffer(received_data)
            return

        self._parser.append_to_hdlc_buffer(received_data)
        if self._parser.extract_data_from_hdlc_frames():
            dlms_objects = self._parser.parse_to_dlms_objects()
