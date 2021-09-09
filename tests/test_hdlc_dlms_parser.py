#
# Copyright (C) 2021 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
import random
import re

from gurux_dlms.objects.GXDLMSObject import GXDLMSObject

from smartmeter_datacollector.smartmeter.cosem import CosemConfig
from smartmeter_datacollector.smartmeter.hdlc_dlms_parser import HdlcDlmsParser

from .utils import *


class TestHdlcParserUnencrypted:
    def test_extract_hdlc_data_framewise(self, unencrypted_valid_data_lg):
        parser = HdlcDlmsParser(CosemConfig("", "", []))

        for frame in unencrypted_valid_data_lg:
            assert not parser.extract_data_from_hdlc_frames()
            parser.append_to_hdlc_buffer(frame)

        assert parser.extract_data_from_hdlc_frames()

    def test_extract_hdlc_data_in_halfframes(self, unencrypted_valid_data_lg):
        parser = HdlcDlmsParser(CosemConfig("", "", []))

        for frame in unencrypted_valid_data_lg:
            frame: bytes
            assert not parser.extract_data_from_hdlc_frames()
            parser.append_to_hdlc_buffer(frame[:int(len(frame)/2)])
            assert not parser.extract_data_from_hdlc_frames()
            parser.append_to_hdlc_buffer(frame[int(len(frame)/2):])

        assert parser.extract_data_from_hdlc_frames()

    def test_extract_hdlc_data_with_random_prefix(self, unencrypted_valid_data_lg):
        parser = HdlcDlmsParser(CosemConfig("", "", []))
        random.seed(123)
        prefix = bytes(random.getrandbits(8) for _ in range(32))
        parser.append_to_hdlc_buffer(prefix)
        for frame in unencrypted_valid_data_lg:
            assert not parser.extract_data_from_hdlc_frames()
            parser.append_to_hdlc_buffer(frame)

        assert parser.extract_data_from_hdlc_frames()


class TestDlmsParserUnencrypted:
    @pytest.fixture
    def valid_hdlc_buffer(self, cosem_config_lg, unencrypted_valid_data_lg) -> HdlcDlmsParser:
        parser = HdlcDlmsParser(cosem_config_lg)
        for frame in unencrypted_valid_data_lg:
            parser.append_to_hdlc_buffer(frame)
            parser.extract_data_from_hdlc_frames()
        return parser

    @pytest.fixture
    def invalid_hdlc_buffer(self, cosem_config_lg, unencrypted_invalid_data_lg) -> HdlcDlmsParser:
        parser = HdlcDlmsParser(cosem_config_lg)
        for frame in unencrypted_invalid_data_lg:
            parser.append_to_hdlc_buffer(frame)
            parser.extract_data_from_hdlc_frames()
        return parser

    def test_parse_hdlc_to_dlms_objects(self, valid_hdlc_buffer: HdlcDlmsParser):
        dlms_objects = valid_hdlc_buffer.parse_to_dlms_objects()

        assert isinstance(dlms_objects, dict)
        assert len(dlms_objects) == 15
        obis_pattern = re.compile(r"(\d+\.){5}\d+")
        for key, value in dlms_objects.items():
            assert isinstance(key, str)
            assert re.match(obis_pattern, key)
            assert isinstance(value, GXDLMSObject)

    def test_parse_dlms_to_meter_data(self, valid_hdlc_buffer: HdlcDlmsParser):
        dlms_objects = valid_hdlc_buffer.parse_to_dlms_objects()
        meter_data = valid_hdlc_buffer.convert_dlms_bundle_to_reader_data(dlms_objects)
        assert isinstance(meter_data, list)
        assert len(meter_data) == 2
        assert any(data.type == MeterDataPointTypes.ACTIVE_POWER_P.value for data in meter_data)
        assert any(data.type == MeterDataPointTypes.ACTIVE_POWER_N.value for data in meter_data)
        assert all(isinstance(data.value, float) for data in meter_data)
        assert all(data.source == "LGZ1030655933512" for data in meter_data)
        assert all(data.timestamp.strftime(r"%m/%d/%y %H:%M:%S") == "07/06/21 14:58:18" for data in meter_data)

    def test_parse_not_parsable_data_to_meter_data(self, invalid_hdlc_buffer: HdlcDlmsParser):
        dlms_objects = invalid_hdlc_buffer.parse_to_dlms_objects()
        meter_data = invalid_hdlc_buffer.convert_dlms_bundle_to_reader_data(dlms_objects)
        assert isinstance(meter_data, list)
        assert len(meter_data) == 0
