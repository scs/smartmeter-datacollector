#
# Copyright (C) 2021 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
import asyncio
import logging
from asyncio.exceptions import CancelledError
from configparser import ConfigParser

import config
import factory

logging.basicConfig(level=logging.WARNING)

CONFIG_PATHS = [
    "./datacollector.ini",
    "/etc/datacollector/datacollector.ini"
]


async def main():
    app_config = config.read_config_files(CONFIG_PATHS)
    set_logging_levels(app_config)

    readers = factory.build_readers(app_config)
    sinks = factory.build_sinks(app_config)
    data_collector = factory.build_collector(readers, sinks)

    await asyncio.gather(*[sink.start() for sink in sinks])

    try:
        await asyncio.gather(
            *[reader.start() for reader in readers],
            data_collector.process_queue(),
            return_exceptions=True)
    except CancelledError:
        logging.info("App shutting down now.")
        await asyncio.gather(*[sink.stop() for sink in sinks])


def set_logging_levels(app_config: ConfigParser) -> None:
    if not app_config.has_section("logging"):
        return
    # configure root logger
    logging.getLogger().setLevel(app_config["logging"].get('default', logging.WARNING))
    # configure individual loggers
    for name, level in app_config["logging"].items():
        logging.getLogger(name).setLevel(level)


if __name__ == '__main__':
    asyncio.run(main(), debug=True)
