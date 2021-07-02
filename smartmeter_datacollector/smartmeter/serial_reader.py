from dataclasses import dataclass
from typing import Union

import serial
from aioserial import AioSerial


@dataclass
class SerialConfig:
    port: str
    baudrate: int = 9600
    data_bits: int = serial.EIGHTBITS
    parity: str = serial.PARITY_NONE
    stop_bits: int = serial.STOPBITS_ONE
    termination: Union[bytes, None] = None


class SerialReader:
    CHUNK_SIZE = 16
    TIMEOUT = 0.2
    
    def __init__(self, serial_config: SerialConfig, callback) -> None:
        self._callback = callback
        self._termination = serial_config.termination
        self._serial = AioSerial(
            port=serial_config.port,
            baudrate=serial_config.baudrate,
            bytesize=serial_config.data_bits,
            parity=serial_config.parity,
            stopbits=serial_config.stop_bits,
            timeout=SerialReader.TIMEOUT
        )

    async def start_and_listen(self) -> None:
        if self._termination:
            await self._read_until()
        else:
            await self._read_chunks()

    async def _read_until(self) -> None:
        while True:
            data: bytes = await self._serial.read_until_async(self._termination, None)
            self._callback(data)

    async def _read_chunks(self) -> None:
        while True:
            data: bytes = await self._serial.read_async(SerialReader.CHUNK_SIZE)
            if data:
                self._callback(data)
