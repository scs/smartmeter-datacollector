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

from smartmeter_datacollector.sinks.mqtt_sink import MqttConfig, MqttDataSink, MqttSinkRlDsp
from smartmeter_datacollector.smartmeter.meter_data import MeterDataBundle, MeterDataPoint, MeterDataPointType
from smartmeter_datacollector.smartmeter.obis import OBISCode

TEST_DATA_POINT_TYPE = MeterDataPointType("TEST_TYPE", "test type", "unit")
TEST_OBIS = OBISCode(0, 1, 2, 3, 4, 5)
TEST_OBIS_2 = OBISCode(1, 1, 2, 8, 0, 255)


@pytest.fixture(autouse=True)
def mocked_mqtt_client(mocker: pytest_mock.MockerFixture):
    mock_client_class = mocker.patch("smartmeter_datacollector.sinks.mqtt_sink.Client", autospec=True)
    return mock_client_class.return_value


@pytest.mark.asyncio
async def test_mqtt_sink_send_datapoint(mocked_mqtt_client):
    config = MqttConfig("localhost")
    sink = MqttDataSink(config)

    timestamp = datetime.now(timezone.utc)
    data_point = MeterDataPoint(TEST_DATA_POINT_TYPE, 1.0, TEST_OBIS)
    data_bundle = MeterDataBundle("test_source", timestamp, [data_point])
    expected_topic = f"smartmeter/test_source/{TEST_DATA_POINT_TYPE.identifier}"
    expected_payload = json.dumps({
        "value": data_point.value,
        "timestamp": int(timestamp.timestamp()),
        "obis": TEST_OBIS.to_short_str(),
    })

    await sink.send(data_bundle)

    mocked_mqtt_client.publish.assert_awaited_with(expected_topic, expected_payload)


@pytest.mark.asyncio
async def test_mqtt_sink_retry_sending_datapoint(mocked_mqtt_client: mock.MagicMock):
    config = MqttConfig("localhost")
    sink = MqttDataSink(config)
    data_point = MeterDataPoint(TEST_DATA_POINT_TYPE, 1.0, TEST_OBIS)
    data_bundle = MeterDataBundle("test_source", datetime.now(timezone.utc), [data_point])

    # Simulate publish raising MqttCodeError the first time, then succeeding
    mocked_mqtt_client.publish.side_effect = [MqttCodeError(MQTT_ERR_NO_CONN), None]

    with mock.patch("smartmeter_datacollector.sinks.mqtt_sink.asyncio.sleep"):
        await sink.send(data_bundle)

    assert mocked_mqtt_client.publish.await_count == 2


@pytest.mark.asyncio
async def test_mqtt_sink_only_retry_sending_3_times(mocked_mqtt_client: mock.MagicMock):
    config = MqttConfig("localhost")
    sink = MqttDataSink(config)
    data_point = MeterDataPoint(TEST_DATA_POINT_TYPE, 1.0, TEST_OBIS)
    data_bundle = MeterDataBundle("test_source", datetime.now(timezone.utc), [data_point])

    mocked_mqtt_client.publish.side_effect = [MqttCodeError(MQTT_ERR_NO_CONN)]*4

    with mock.patch("smartmeter_datacollector.sinks.mqtt_sink.asyncio.sleep"):
        await sink.send(data_bundle)

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


@pytest.mark.asyncio
async def test_mqtt_sink_rldsp_send_publishes_single_message(mocked_mqtt_client: mock.MagicMock):
    config = MqttConfig("localhost")
    sink = MqttSinkRlDsp(config)

    timestamp = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
    data_point = MeterDataPoint(TEST_DATA_POINT_TYPE, 42.0, TEST_OBIS)
    data_bundle = MeterDataBundle("meter1", timestamp, [data_point])

    await sink.send(data_bundle)

    assert mocked_mqtt_client.publish.await_count == 1


@pytest.mark.asyncio
async def test_mqtt_sink_rldsp_send_uses_correct_topic(mocked_mqtt_client: mock.MagicMock):
    config = MqttConfig("localhost")
    sink = MqttSinkRlDsp(config)

    timestamp = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
    data_point = MeterDataPoint(TEST_DATA_POINT_TYPE, 42.0, TEST_OBIS)
    data_bundle = MeterDataBundle("meter1", timestamp, [data_point])
    expected_topic = "dt/building/meter1/ds"

    await sink.send(data_bundle)

    mocked_mqtt_client.publish.assert_awaited_once_with(expected_topic, mock.ANY)


@pytest.mark.asyncio
async def test_mqtt_sink_rldsp_send_multiple_datapoints_single_publish(mocked_mqtt_client: mock.MagicMock):
    config = MqttConfig("localhost")
    sink = MqttSinkRlDsp(config)

    timestamp = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
    data_points = [
        MeterDataPoint(TEST_DATA_POINT_TYPE, 100.0, TEST_OBIS),
        MeterDataPoint(TEST_DATA_POINT_TYPE, 200.0, TEST_OBIS_2),
    ]
    data_bundle = MeterDataBundle("meter1", timestamp, data_points)

    await sink.send(data_bundle)

    assert mocked_mqtt_client.publish.await_count == 1


def test_mqtt_sink_rldsp_to_mqtt_payload_contains_timestamp():
    timestamp = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
    data_point = MeterDataPoint(TEST_DATA_POINT_TYPE, 42.0, TEST_OBIS)
    data_bundle = MeterDataBundle("meter1", timestamp, [data_point])

    payload = json.loads(MqttSinkRlDsp.to_mqtt_payload(data_bundle))

    assert payload["meter"]["ts"] == timestamp.isoformat()


def test_mqtt_sink_rldsp_to_mqtt_payload_contains_obis_values():
    timestamp = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
    data_points = [
        MeterDataPoint(TEST_DATA_POINT_TYPE, 100.0, TEST_OBIS),
        MeterDataPoint(TEST_DATA_POINT_TYPE, 200.0, TEST_OBIS_2),
    ]
    data_bundle = MeterDataBundle("meter1", timestamp, data_points)

    payload = json.loads(MqttSinkRlDsp.to_mqtt_payload(data_bundle))

    assert payload["meter"][TEST_OBIS.to_short_str()] == 100.0
    assert payload["meter"][TEST_OBIS_2.to_short_str()] == 200.0


def test_mqtt_sink_rldsp_build_topic_name():
    config = MqttConfig("localhost")
    sink = MqttSinkRlDsp(config)
    timestamp = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
    data_bundle = MeterDataBundle("my_meter", timestamp, [])

    topic = sink.build_topic_name(data_bundle)

    assert topic == "dt/building/my_meter/ds"
