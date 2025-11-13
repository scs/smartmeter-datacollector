#
# Copyright (C) 2024 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
import configparser
import json
from datetime import datetime, timezone
from unittest import mock

import pytest
import pytest_mock
from aiomqtt import MqttCodeError
from paho.mqtt.client import MQTT_ERR_NO_CONN

from smartmeter_datacollector.sinks.mqtt_sink import MqttConfig, MqttDataSink
from smartmeter_datacollector.smartmeter.meter_data import MeterDataPoint, MeterDataPointType

TEST_DATA_POINT_TYPE = MeterDataPointType("TEST_TYPE", "test type", "unit")


@pytest.fixture(autouse=True)
def mocked_mqtt_client(mocker: pytest_mock.MockerFixture):
    mock_client_class = mocker.patch("smartmeter_datacollector.sinks.mqtt_sink.Client", autospec=True)
    return mock_client_class.return_value


@pytest.mark.asyncio
async def test_mqtt_sink_send_datapoint(mocked_mqtt_client):
    config = MqttConfig("localhost")
    sink = MqttDataSink(config)

    data_point = MeterDataPoint(TEST_DATA_POINT_TYPE, 1.0, "test_source", datetime.now(timezone.utc))
    expected_topic = f"smartmeter/test_source/{TEST_DATA_POINT_TYPE.identifier}"
    expected_payload = json.dumps({
        "value": data_point.value,
        "timestamp": int(data_point.timestamp.timestamp()),
    })

    await sink.send(data_point)

    mocked_mqtt_client.publish.assert_awaited_with(expected_topic, expected_payload)


@pytest.mark.asyncio
async def test_mqtt_sink_retry_sending_datapoint(mocked_mqtt_client: mock.MagicMock):
    config = MqttConfig("localhost")
    sink = MqttDataSink(config)
    data_point = MeterDataPoint(TEST_DATA_POINT_TYPE, 1.0, "test_source", datetime.now(timezone.utc))

    # Simulate publish raising MqttCodeError the first time, then succeeding
    mocked_mqtt_client.publish.side_effect = [MqttCodeError(MQTT_ERR_NO_CONN), None]

    with mock.patch("smartmeter_datacollector.sinks.mqtt_sink.asyncio.sleep"):
        await sink.send(data_point)

    assert mocked_mqtt_client.publish.await_count == 2


@pytest.mark.asyncio
async def test_mqtt_sink_only_retry_sending_3_times(mocked_mqtt_client: mock.MagicMock):
    config = MqttConfig("localhost")
    sink = MqttDataSink(config)
    data_point = MeterDataPoint(TEST_DATA_POINT_TYPE, 1.0, "test_source", datetime.now(timezone.utc))

    mocked_mqtt_client.publish.side_effect = [MqttCodeError(MQTT_ERR_NO_CONN)]*4

    with mock.patch("smartmeter_datacollector.sinks.mqtt_sink.asyncio.sleep"):
        await sink.send(data_point)

    assert mocked_mqtt_client.publish.await_count == 3


@mock.patch("smartmeter_datacollector.sinks.mqtt_sink.Client", new_callable=mock.MagicMock)
def test_mqtt_config_unencrypted_unauthorized(_: mock.MagicMock):
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


@mock.patch("smartmeter_datacollector.sinks.mqtt_sink.Client", new_callable=mock.MagicMock)
def test_mqtt_config_encrypted_unauthorized(_: mock.MagicMock):
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


@mock.patch("smartmeter_datacollector.sinks.mqtt_sink.Client", new_callable=mock.MagicMock)
def test_mqtt_config_encrypted_authorized_user_pass(_: mock.MagicMock):
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


@mock.patch("smartmeter_datacollector.sinks.mqtt_sink.Client", new_callable=mock.MagicMock)
def test_mqtt_config_encrypted_authorized_client_cert(_: mock.MagicMock):
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
