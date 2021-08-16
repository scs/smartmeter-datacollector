#
# Copyright (C) 2021 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
import json
import logging

from asyncio_mqtt import Client
from asyncio_mqtt.client import ProtocolVersion
from asyncio_mqtt.error import MqttCodeError, MqttError
from paho.mqtt.client import MQTT_ERR_NO_CONN
from smartmeter.reader_data import ReaderDataPoint

from .data_sink import DataSink

LOGGER = logging.getLogger("sink")


class MqttDataSink(DataSink):
    TIMEOUT = 3

    def __init__(self, broker_host: str) -> None:
        self._client = Client(
            hostname=broker_host,
            port=1883,
            clean_session=True,
            protocol=ProtocolVersion.V311
        )

    async def start(self) -> None:
        if await self._connect_to_server():
            LOGGER.info("Connected to MQTT broker.")

    async def stop(self) -> None:
        await self._disconnect_from_server()
        LOGGER.info("Disconnected from MQTT broker.")

    async def send(self, data_point: ReaderDataPoint) -> None:
        topic = MqttDataSink.get_topic_name_for_datapoint(data_point)
        dp_json = self.data_point_to_mqtt_json(data_point)
        try:
            await self._client.publish(topic, dp_json)
            LOGGER.debug("%s sent to MQTT broker.", dp_json)
        except ValueError as ex:
            LOGGER.error("MQTT payload or topic is invalid: '%s'", ex)
        except MqttCodeError as ex:
            if ex.rc == MQTT_ERR_NO_CONN:
                if await self._connect_to_server():
                    LOGGER.info("Reconnected to MQTT broker.")
                    try:
                        await self._client.publish(topic, dp_json)
                        LOGGER.debug("%s sent to MQTT broker.", dp_json)
                    except MqttError:
                        LOGGER.warning("MQTT message not sent.")
            else:
                LOGGER.error("MQTT message sending error: '%s'", ex)
        except MqttError as ex:
            LOGGER.error("MQTT message sending error: '%s'", ex)

    async def _connect_to_server(self) -> bool:
        try:
            await self._client.connect(timeout=self.TIMEOUT)
        except MqttError as ex:
            LOGGER.error(ex)
            return False
        return True

    async def _disconnect_from_server(self) -> None:
        try:
            await self._client.disconnect(timeout=self.TIMEOUT)
        except MqttError as ex:
            LOGGER.error(ex)
            await self._client.force_disconnect()

    @staticmethod
    def get_topic_name_for_datapoint(data_point: ReaderDataPoint) -> str:
        return f"smartmeter/{data_point.source}/{data_point.type.identifier}"

    @staticmethod
    def data_point_to_mqtt_json(data_point: ReaderDataPoint) -> str:
        return json.dumps({
            "value": data_point.value,
            "timestamp": int(data_point.timestamp.timestamp())
        })
