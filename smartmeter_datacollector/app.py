import asyncio
import logging

from smartmeter.lge450 import LGE450

logging.basicConfig(level=logging.DEBUG)

async def main():
    meter = LGE450("/dev/ttyUSB0")
    await meter.start()

if __name__ == '__main__':
    asyncio.run(main(), debug=True)
