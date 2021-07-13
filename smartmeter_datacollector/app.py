import asyncio
import logging

from collector import Collector
from sinks.logger_sink import LoggerSink
from smartmeter.iskraam550 import IskraAM550
from smartmeter.lge450 import LGE450

logging.basicConfig(level=logging.DEBUG)


async def main():
    # meter = LGE450("/dev/ttyUSB1")
    meter = IskraAM550("/dev/ttyUSB0")
    collector = Collector()
    sink = LoggerSink("DataLogger")

    collector.register_sink(sink)
    meter.register(collector)

    await asyncio.gather(
        meter.start(),
        collector.process_queue())

if __name__ == '__main__':
    asyncio.run(main(), debug=True)
