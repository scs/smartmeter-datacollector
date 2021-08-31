import json
from datetime import datetime

import pytest
from asyncio_mqtt.error import MqttCodeError
from paho.mqtt.client import MQTT_ERR_NO_CONN
from pytest_mock.plugin import MockerFixture

from smartmeter_datacollector.sinks.mqtt_sink import MqttConfig, MqttDataSink
from smartmeter_datacollector.smartmeter.meter_data import MeterDataPoint, MeterDataPointType

TEST_TYPE = MeterDataPointType("TEST_TYPE", "test type", "unit")


@pytest.mark.asyncio
async def test_mqtt_sink_start_stop(mocker: MockerFixture):
    config = MqttConfig("localhost")
    sink = MqttDataSink(config)
    client_mock = mocker.patch.object(sink, "_client", autospec=True)

    await sink.start()
    client_mock.connect.assert_called_once()

    await sink.stop()
    client_mock.disconnect.assert_called_once()


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

    client_mock.publish.assert_called_once_with(expected_topic, expected_payload)


@pytest.mark.asyncio
async def test_mqtt_sink_send_reconnect_when_not_started(mocker: MockerFixture):
    config = MqttConfig("localhost")
    sink = MqttDataSink(config)
    client_mock = mocker.patch.object(sink, "_client", autospec=True)
    data_point = MeterDataPoint(TEST_TYPE, 1.0, "test_source", datetime.utcnow())

    client_mock.publish.side_effect = MqttCodeError(MQTT_ERR_NO_CONN)
    await sink.send(data_point)

    client_mock.publish.assert_called()
    assert client_mock.publish.call_count == 2
    client_mock.connect.assert_called_once()
