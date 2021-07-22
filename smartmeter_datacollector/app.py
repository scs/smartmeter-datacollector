import asyncio
import logging

from collector import Collector
from sinks.logger_sink import LoggerSink
from sinks.mqtt_sink import MqttDataSink
from smartmeter.iskraam550 import IskraAM550
from smartmeter.lge450 import LGE450

logging.basicConfig(level=logging.DEBUG)


async def main():
    meter = LGE450("/dev/ttyUSB0")
    # meter = IskraAM550("/dev/ttyUSB0")
    collector = Collector()
    logger_sink = LoggerSink("DataLogger")
    mqtt_sink = MqttDataSink("localhost")
    await mqtt_sink.start()

    collector.register_sink(logger_sink)
    collector.register_sink(mqtt_sink)
    meter.register(collector)

    await asyncio.gather(
        meter.start(),
        collector.process_queue())

if __name__ == '__main__':
    asyncio.run(main(), debug=True)
