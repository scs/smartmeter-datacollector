#
# Copyright (C) 2021 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
import json
import logging
import ssl
from configparser import SectionProxy
from dataclasses import dataclass
from typing import Optional

from asyncio_mqtt import Client
from asyncio_mqtt.client import ProtocolVersion
from asyncio_mqtt.error import MqttCodeError, MqttError
from paho.mqtt.client import MQTT_ERR_NO_CONN

from ..smartmeter.meter_data import MeterDataPoint
from .data_sink import DataSink

LOGGER = logging.getLogger("sink")


# pylint: disable=too-many-instance-attributes
@dataclass
class MqttConfig:
    broker_host: str
    port: int = 1883
    use_tls: bool = False
    username: Optional[str] = None
    password: Optional[str] = None
    client_id: Optional[str] = None
    ca_cert_path: Optional[str] = None
    check_hostname: bool = True
    client_cert_path: Optional[str] = None
    client_key_path: Optional[str] = None

    def with_tls(self, ca_cert_path: Optional[str] = None, check_hostname: bool = True) -> "MqttConfig":
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
        mqtt_cfg = MqttConfig(config.get("host"), config.getint("port", 1883))
        if config.getboolean("tls", fallback=False):
            mqtt_cfg.with_tls(config.get("ca_file_path"), config.getboolean("check_hostname", True))
        if config.get("username") and config.get("password"):
            mqtt_cfg.with_user_pass_auth(
                config.get("username"),
                config.get("password"))
        if config.get("client_cert_path") and config.get("client_key_path"):
            mqtt_cfg.with_client_cert_auth(
                config.get("client_cert_path"),
                config.get("client_key_path")
            )
        return mqtt_cfg


class MqttDataSink(DataSink):
    TIMEOUT = 3

    def __init__(self, config: MqttConfig) -> None:
        tls_context = None
        if config.use_tls:
            tls_context = self._build_ssl_context(
                config.ca_cert_path,
                config.check_hostname,
                config.client_cert_path,
                config.client_key_path)

        user_pass_auth = {}
        if config.username and config.password:
            user_pass_auth["username"] = config.username
            user_pass_auth["password"] = config.password

        self._client = Client(
            hostname=config.broker_host,
            port=config.port,
            client_id=config.client_id,
            tls_context=tls_context,
            protocol=ProtocolVersion.V311,
            clean_session=True,
            **user_pass_auth)

    @staticmethod
    def _build_ssl_context(
        ca_file_path: Optional[str] = None,
        check_hostname: bool = True,
        client_cert_path: Optional[str] = None,
        client_key_path: Optional[str] = None
    ) -> ssl.SSLContext:
        context = ssl.create_default_context(cafile=ca_file_path)

        if ca_file_path:
            context.check_hostname = check_hostname

        if client_cert_path:
            try:
                context.load_cert_chain(client_cert_path, client_key_path, None)
            except ssl.SSLError as ex:
                LOGGER.error("Client certificate does not match with the key and is ignored. '%s'", ex)
        return context

    async def start(self) -> None:
        if await self._connect_to_server():
            LOGGER.info("Connected to MQTT broker.")

    async def stop(self) -> None:
        await self._disconnect_from_server()
        LOGGER.info("Disconnected from MQTT broker.")

    async def send(self, data_point: MeterDataPoint) -> None:
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
    def get_topic_name_for_datapoint(data_point: MeterDataPoint) -> str:
        return f"smartmeter/{data_point.source}/{data_point.type.identifier}"

    @staticmethod
    def data_point_to_mqtt_json(data_point: MeterDataPoint) -> str:
        return json.dumps({
            "value": data_point.value,
            "timestamp": int(data_point.timestamp.timestamp())
        })
