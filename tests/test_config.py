#
# Copyright (C) 2022 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
from configparser import ConfigParser
from pathlib import Path

from smartmeter_datacollector import config


def test_default_config_has_sections():
    def_conf = config.get_default_config()
    assert isinstance(def_conf, ConfigParser)
    assert def_conf.has_section("reader0")
    assert def_conf.get("reader0", "type") == "lge450"

    assert def_conf.has_section("sink0")
    assert def_conf.get("sink0", "type") == "logger"
    assert def_conf.has_section("sink1")
    assert def_conf.get("sink1", "type") == "mqtt"

    assert def_conf.has_section("logging")


def test_write_default_config(tmp_path: Path):
    file_path = tmp_path / "cfg.ini"
    config.write_default_config(str(file_path))

    assert file_path.is_file()
    assert len(file_path.read_text(encoding="utf-8")) > 0


def test_read_config(tmp_path: Path):
    file_path = tmp_path / "cfg.ini"
    CFG = """
    [reader0]
    type = lge450
    port = /test
    key = 
    """
    file_path.write_text(CFG, encoding="utf-8")

    cfg = config.read_config_files(str(file_path))
    assert isinstance(cfg, ConfigParser)

    assert cfg.has_section("reader0")
    assert cfg.get("reader0", "type") == "lge450"
    assert cfg.get("reader0", "port") == "/test"
    assert cfg.get("reader0", "key") == ""
