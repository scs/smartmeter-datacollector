import logging

from asyncio_mqtt import Client
from asyncio_mqtt.client import ProtocolVersion
from asyncio_mqtt.error import MqttError
from smartmeter.reader_data import ReaderDataPoint

from .data_sink import DataSink

LOGGER = logging.getLogger("MQTTDataSink")


class MqttDataSink(DataSink):
    def __init__(self, broker_host: str) -> None:
        self._client = Client(
            hostname=broker_host,
            port=1883,
            clean_session=True,
            protocol=ProtocolVersion.V311
        )
        self._connected = False

    async def start(self) -> None:
        if self._connected:
            return
        try:
            await self._client.connect()
        except MqttError as ex:
            LOGGER.error(ex)
            return
        self._connected = True

    async def stop(self) -> None:
        if not self._connected:
            return
        try:
            await self._client.disconnect()
        except MqttError as ex:
            LOGGER.error(ex)
            await self._client.force_disconnect()
        self._connected = False

    async def send(self, data_point: ReaderDataPoint) -> None:
        topic = MqttDataSink.get_topic_name_for_datapoint(data_point)
        try:
            dp_json = data_point.to_json()
            LOGGER.debug("Sending DP over MQTT: %s", dp_json)
            await self._client.publish(topic, dp_json)
        except (MqttError, ValueError) as ex:
            LOGGER.error("MQTT message could not be sent. '%s'", ex)

    @staticmethod
    def get_topic_name_for_datapoint(data_point: ReaderDataPoint) -> str:
        return f"smartmeter/{data_point.source}/{data_point.type.id}"
