#
# Copyright (C) 2021 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
from configparser import ConfigParser
from typing import List

from collector import Collector
from config import InvalidConfigError
from sinks.data_sink import DataSink
from sinks.logger_sink import LoggerSink
from sinks.mqtt_sink import MqttDataSink
from smartmeter.iskraam550 import IskraAM550
from smartmeter.lge450 import LGE450
from smartmeter.reader import Reader


def build_readers(config: ConfigParser) -> List[Reader]:
    readers = []
    for section_name in filter(lambda sec: sec.startswith("reader"), config.sections()):
        reader_config = config[section_name]
        reader_type = reader_config.get('type')

        if reader_type == "lge450":
            readers.append(LGE450(
                port=reader_config.get('port', "/dev/ttyUSB0"),
                decryption_key=reader_config.get('key')
            ))
        elif reader_type == "iskraam550":
            readers.append(IskraAM550(
                port=reader_config.get('port', "/dev/ttyUSB0")
            ))
        else:
            raise InvalidConfigError(f"'type' is invalid or missing: {reader_type}")
    return readers


def build_sinks(config: ConfigParser) -> List[DataSink]:
    sinks = []
    for section_name in filter(lambda sec: sec.startswith("sink"), config.sections()):
        sink_config = config[section_name]
        sink_type = sink_config.get('type')

        if sink_type == "logger":
            sinks.append(LoggerSink(
                logger_name=sink_config.get('name', "DataLogger")
            ))
        elif sink_type == "mqtt":
            sinks.append(MqttDataSink(
                broker_host=sink_config.get('host', "localhost")
            ))
        else:
            raise InvalidConfigError(f"'type' is invalid or missing: {sink_type}")
    return sinks


def build_collector(readers: List[Reader], sinks: List[DataSink]) -> Collector:
    collector = Collector()

    for sink in sinks:
        collector.register_sink(sink)
    for reader in readers:
        reader.register(collector)
    return collector
