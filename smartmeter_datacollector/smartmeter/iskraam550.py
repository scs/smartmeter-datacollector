import logging

from dsmr_parser.clients.telegram_buffer import TelegramBuffer
from dsmr_parser.exceptions import ParseError, InvalidChecksumError
from dsmr_parser.objects import Telegram
from dsmr_parser.parsers import TelegramParser
from dsmr_parser.clients import SERIAL_SETTINGS_V5
from dsmr_parser import telegram_specifications

from smartmeter.serial_reader import SerialConfig, SerialReader
from .reader import Reader

LOGGER = logging.getLogger("smartmeter")


class IskraAM550(Reader):
    def __init__(self, port: str) -> None:
        super().__init__()

        serial_config = SerialConfig(
            port=port,
            baudrate=SERIAL_SETTINGS_V5['baudrate'],
            data_bits=SERIAL_SETTINGS_V5['bytesize'],
            parity=SERIAL_SETTINGS_V5['parity'],
            stop_bits=SERIAL_SETTINGS_V5['stopbits']
        )
        self._serial = SerialReader(serial_config, self._data_received)
        self._telegram_buffer = TelegramBuffer()
        self._telegram_parser = TelegramParser(telegram_specifications.V5, True)

    async def start(self) -> None:
        await self._serial.start_and_listen()

    def _data_received(self, received_data: bytes) -> None:
        if not received_data:
            return
        self._telegram_buffer.append(received_data.decode('ascii'))

        for telegram in self._telegram_buffer.get_all():
            try:
                parsed_telegram = self._telegram_parser.parse(telegram)
                LOGGER.debug("Telegram: %s", str(parsed_telegram))
                # OR
                telegram_obj = Telegram(telegram, self._telegram_parser, telegram_specifications.V5)
            except (ParseError, InvalidChecksumError) as ex:
                LOGGER.error("Unable to parse telegram. '%s'", ex)
