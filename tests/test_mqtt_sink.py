#
# Copyright (C) 2022 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
import configparser
import json
import sys
from datetime import datetime
from unittest import mock

import pytest
from asyncio_mqtt.error import MqttCodeError
from paho.mqtt.client import MQTT_ERR_NO_CONN
from pytest_mock.plugin import MockerFixture

from smartmeter_datacollector.sinks.mqtt_sink import MqttConfig, MqttDataSink
from smartmeter_datacollector.smartmeter.meter_data import MeterDataPoint, MeterDataPointType

TEST_TYPE = MeterDataPointType("TEST_TYPE", "test type", "unit")


@pytest.mark.skipif(sys.version_info < (3, 8), reason="Python3.7 does not support AsyncMock.")
@pytest.mark.asyncio
async def test_mqtt_sink_start_stop(mocker: MockerFixture):
    config = MqttConfig("localhost")
    sink = MqttDataSink(config)
    client_mock = mocker.patch.object(sink, "_client", autospec=True)

    await sink.start()
    client_mock.connect.assert_awaited_once()

    await sink.stop()
    client_mock.disconnect.assert_awaited_once()


@pytest.mark.skipif(sys.version_info < (3, 8), reason="Python3.7 does not support AsyncMock.")
@pytest.mark.asyncio
async def test_mqtt_sink_send_point_when_started(mocker: MockerFixture):
    config = MqttConfig("localhost")
    sink = MqttDataSink(config)
    client_mock = mocker.patch.object(sink, "_client", autospec=True)
    data_point = MeterDataPoint(TEST_TYPE, 1.0, "test_source", datetime.utcnow())
    expected_topic = f"smartmeter/test_source/{TEST_TYPE.identifier}"
    expected_payload = json.dumps({
        "value": data_point.value,
        "timestamp": int(data_point.timestamp.timestamp()),
    })

    await sink.start()
    await sink.send(data_point)

    client_mock.publish.assert_awaited_once_with(expected_topic, expected_payload)


@pytest.mark.skipif(sys.version_info < (3, 8), reason="Python3.7 does not support AsyncMock.")
@pytest.mark.asyncio
async def test_mqtt_sink_send_reconnect_when_not_started(mocker: MockerFixture):
    config = MqttConfig("localhost")
    sink = MqttDataSink(config)
    client_mock = mocker.patch.object(sink, "_client", autospec=True)
    data_point = MeterDataPoint(TEST_TYPE, 1.0, "test_source", datetime.utcnow())

    client_mock.publish.side_effect = MqttCodeError(MQTT_ERR_NO_CONN)
    await sink.send(data_point)

    client_mock.publish.assert_awaited()
    assert client_mock.publish.await_count == 2
    client_mock.connect.assert_awaited_once()


def test_mqtt_config_unencrypted_unauthorized():
    cfg_parser = configparser.ConfigParser()
    cfg_parser.read_dict({
        "sink": {
            'type': "mqtt",
            'host': "localhost",
            'port': 1883,
        }
    })
    sink_section = cfg_parser["sink"]
    cfg = MqttConfig.from_sink_config(sink_section)

    assert cfg.broker_host == sink_section.get("host")
    assert cfg.port == sink_section.getint("port")
    assert cfg.use_tls == False
    assert cfg.username is None
    assert cfg.password is None
    assert cfg.client_cert_path is None
    assert cfg.client_key_path is None

    sink = MqttDataSink(cfg)


def test_mqtt_config_encrypted_unauthorized():
    cfg_parser = configparser.ConfigParser()
    cfg_parser.read_dict({
        "sink": {
            'type': "mqtt",
            'host': "http://secure-host.com",
            'port': 8883,
            'tls': True,
            'ca_file_path': "/test/path",
            'check_hostname': False,
        }
    })
    sink_section = cfg_parser["sink"]
    cfg = MqttConfig.from_sink_config(sink_section)

    assert cfg.broker_host == sink_section.get("host")
    assert cfg.port == sink_section.getint("port")
    assert cfg.use_tls == True
    assert cfg.ca_cert_path == sink_section.get("ca_file_path")
    assert cfg.check_hostname == False
    assert cfg.username is None

    with mock.patch("smartmeter_datacollector.sinks.mqtt_sink.ssl"):
        sink = MqttDataSink(cfg)


def test_mqtt_config_encrypted_authorized_user_pass():
    cfg_parser = configparser.ConfigParser()
    cfg_parser.read_dict({
        "sink": {
            'type': "mqtt",
            'host': "http://secure-host.com",
            'port': 8883,
            'tls': True,
            'ca_file_path': "",
            'check_hostname': True,
            'username': "testuser",
            'password': "testpassword",
            'client_cert_path': "",
        }
    })
    sink_section = cfg_parser["sink"]
    cfg = MqttConfig.from_sink_config(sink_section)

    assert cfg.use_tls == True
    assert cfg.ca_cert_path == sink_section.get("ca_file_path")
    assert cfg.check_hostname == True
    assert cfg.username == sink_section.get("username")
    assert cfg.password == sink_section.get("password")
    assert cfg.client_cert_path is None
    assert cfg.client_key_path is None

    sink = MqttDataSink(cfg)


def test_mqtt_config_encrypted_authorized_client_cert():
    cfg_parser = configparser.ConfigParser()
    cfg_parser.read_dict({
        "sink": {
            'type': "mqtt",
            'host': "http://secure-host.com",
            'port': 8883,
            'tls': True,
            'ca_file_path': "/test/path",
            'check_hostname': True,
            'username': "",
            'client_cert_path': "/path/to/cert",
            'client_key_path': "rel/path/to/key",
        }
    })
    sink_section = cfg_parser["sink"]
    cfg = MqttConfig.from_sink_config(sink_section)

    assert cfg.use_tls == True
    assert cfg.ca_cert_path == sink_section.get("ca_file_path")
    assert cfg.check_hostname == True
    assert cfg.username is None
    assert cfg.password is None
    assert cfg.client_cert_path == sink_section.get("client_cert_path")
    assert cfg.client_key_path == sink_section.get("client_key_path")

    with mock.patch("smartmeter_datacollector.sinks.mqtt_sink.ssl"):
        sink = MqttDataSink(cfg)
