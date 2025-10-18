#
# Copyright (C) 2024 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
import asyncio
import json
import logging
import ssl
from configparser import SectionProxy
from dataclasses import dataclass
from typing import Optional

from aiomqtt import Client, MqttCodeError, MqttError

from smartmeter_datacollector.sinks.data_sink import DataSink
from smartmeter_datacollector.smartmeter.meter_data import MeterDataPoint

LOGGER = logging.getLogger("sink")


# pylint: disable=too-many-instance-attributes
@dataclass
class MqttConfig:
    broker_host: str
    port: int = 1883
    use_tls: bool = False
    username: Optional[str] = None
    password: Optional[str] = None
    ca_cert_path: Optional[str] = None
    check_hostname: bool = True
    client_cert_path: Optional[str] = None
    client_key_path: Optional[str] = None

    def with_tls(
        self, ca_cert_path: Optional[str] = None, check_hostname: bool = True
    ) -> "MqttConfig":
        self.use_tls = True
        self.ca_cert_path = ca_cert_path
        self.check_hostname = check_hostname
        return self

    def with_user_pass_auth(self, username: str, password: str) -> "MqttConfig":
        self.username = username
        self.password = password
        return self

    def with_client_cert_auth(self, cert_path: str, key_path: str) -> "MqttConfig":
        self.use_tls = True
        self.client_cert_path = cert_path
        self.client_key_path = key_path
        return self

    @staticmethod
    def from_sink_config(config: SectionProxy) -> "MqttConfig":
        host = config.get("host")
        if host is None:
            raise ValueError("MQTT config: 'host' must be set")
        port = config.getint("port", 1883)
        mqtt_cfg = MqttConfig(host, port)
        if config.getboolean("tls", fallback=False):
            mqtt_cfg.with_tls(
                config.get("ca_file_path"), config.getboolean("check_hostname", True)
            )
        username = config.get("username")
        password = config.get("password")
        if username is not None and password is not None:
            mqtt_cfg.with_user_pass_auth(username, password)
        client_cert_path = config.get("client_cert_path")
        client_key_path = config.get("client_key_path")
        if client_cert_path is not None and client_key_path is not None:
            mqtt_cfg.with_client_cert_auth(str(client_cert_path), str(client_key_path))
        return mqtt_cfg


class MqttDataSink(DataSink):
    TIMEOUT = 3
    RETRIES = 2

    def __init__(self, config: MqttConfig) -> None:
        tls_context = None
        if config.use_tls:
            tls_context = self._build_ssl_context(
                config.ca_cert_path,
                config.check_hostname,
                config.client_cert_path,
                config.client_key_path,
            )

        self._client = Client(
            hostname=config.broker_host,
            port=config.port,
            username=config.username,
            password=config.password,
            timeout=self.TIMEOUT,
            tls_context=tls_context,
        )

        self._client_task: Optional[asyncio.Task] = None

    @staticmethod
    def _build_ssl_context(
        ca_file_path: Optional[str] = None,
        check_hostname: bool = True,
        client_cert_path: Optional[str] = None,
        client_key_path: Optional[str] = None,
    ) -> ssl.SSLContext:
        context = ssl.create_default_context(cafile=ca_file_path)

        if ca_file_path:
            context.check_hostname = check_hostname

        if client_cert_path:
            try:
                context.load_cert_chain(client_cert_path, client_key_path, None)
            except ssl.SSLError as ex:
                LOGGER.error("Client certificate does not match with the key and is ignored ('%s')", ex)
        return context

    async def start(self) -> None:
        if self._client_task is not None:
            LOGGER.warning("MQTT client task is already running")
            return
        self._client_task = asyncio.create_task(self._connection_handler())
        LOGGER.info("Connecting to MQTT broker...")

    async def stop(self) -> None:
        if self._client_task is None:
            LOGGER.warning("MQTT client task is not running")
            return
        LOGGER.info("Disconnecting from MQTT broker...")
        self._client_task.cancel()
        try:
            await self._client_task
        except asyncio.CancelledError:
            pass
        self._client_task = None
        LOGGER.info("Disconnected from MQTT broker")

    async def send(self, data_point: MeterDataPoint) -> None:
        topic = MqttDataSink.get_topic_name_for_datapoint(data_point)
        dp_json = self.data_point_to_mqtt_json(data_point)

        await self._publish_with_retries(topic, dp_json, retries=self.RETRIES)

    async def _connection_handler(self) -> None:
        while True:
            try:
                async with self._client:
                    LOGGER.info("Connected to MQTT broker using client ID '%s'", self._client.identifier)
                    async for msg in self._client.messages:
                        # just used to keep the connection alive; no messages are expected
                        LOGGER.debug("Received message on topic '%s': %s", msg.topic, msg.payload)
            except MqttError:
                LOGGER.warning("No connection to MQTT broker. Reconnecting in 1 second...")
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                LOGGER.debug("MQTT client task cancelled")
                break

    async def _publish_with_retries(self, topic: str, payload: str, retries: int = 1) -> None:
        for attempt in range(retries + 1):
            try:
                await self._client.publish(topic, payload)
                LOGGER.debug("Published MQTT msg with topic '%s': %s", topic, payload)
                return
            except ValueError as ex:
                LOGGER.error("MQTT payload or topic is invalid: '%s'", ex)
                return
            except TimeoutError:
                LOGGER.warning("MQTT publish attempt %d failed: not connected to broker", attempt + 1)
            except (MqttCodeError, MqttError) as ex:
                LOGGER.warning("MQTT publish attempt %d failed: %s", attempt + 1, ex)
            if attempt < retries:
                await asyncio.sleep(1)

        LOGGER.error("Failed to publish MQTT msg with topic '%s' after %d attempts. Discarding msg",
                     topic, retries + 1)

    @staticmethod
    def get_topic_name_for_datapoint(data_point: MeterDataPoint) -> str:
        return f"smartmeter/{data_point.source}/{data_point.type.identifier}"

    @staticmethod
    def data_point_to_mqtt_json(data_point: MeterDataPoint) -> str:
        return json.dumps(
            {
                "value": data_point.value,
                "timestamp": int(data_point.timestamp.timestamp()),
            }
        )
