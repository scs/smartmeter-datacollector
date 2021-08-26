#
# Copyright (C) 2021 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
import argparse
import asyncio
import logging
from asyncio.exceptions import CancelledError
from configparser import ConfigParser

from . import config, factory

logging.basicConfig(level=logging.WARNING)


async def build_and_start(app_config: ConfigParser):
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


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Smartmeter Datacollector", add_help=True)
    parser.add_argument(
        '-c', '--config', help="File path of the configuration (.ini) file.", default="./datacollector.ini")
    parser.add_argument(
        '-d', '--dev', help="Development mode", action='store_true')
    return parser.parse_args()


def main():
    args = parse_arguments()
    debug_mode = True if args.dev else False
    app_config = config.read_config_files(args.config)
    set_logging_levels(app_config)
    asyncio.run(build_and_start(app_config), debug=debug_mode)
