#
# Copyright (C) 2022 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
import random
import re

from gurux_dlms.objects.GXDLMSObject import GXDLMSObject

from smartmeter_datacollector.smartmeter.cosem import Cosem
from smartmeter_datacollector.smartmeter.hdlc_dlms_parser import HdlcDlmsParser

from .utils import *


class TestHdlcParserUnencrypted:
    def test_extract_hdlc_data_framewise(self, unencrypted_valid_data_lg: List[bytes]):
        parser = HdlcDlmsParser(Cosem("", []))

        for frame in unencrypted_valid_data_lg:
            assert not parser.extract_data_from_hdlc_frames()
            parser.append_to_hdlc_buffer(frame)

        assert parser.extract_data_from_hdlc_frames()

    def test_extract_hdlc_data_in_halfframes(self, unencrypted_valid_data_lg: List[bytes]):
        parser = HdlcDlmsParser(Cosem("", []))

        for frame in unencrypted_valid_data_lg:
            frame: bytes
            assert not parser.extract_data_from_hdlc_frames()
            parser.append_to_hdlc_buffer(frame[:int(len(frame)/2)])
            assert not parser.extract_data_from_hdlc_frames()
            parser.append_to_hdlc_buffer(frame[int(len(frame)/2):])

        assert parser.extract_data_from_hdlc_frames()


class TestDlmsParserUnencrypted:
    def test_hdlc_to_dlms_objects_with_pushlist(self, unencrypted_valid_data_lg: List[bytes], cosem_config_lg: Cosem):
        parser = prepare_parser(unencrypted_valid_data_lg, cosem_config_lg)
        dlms_objects = parser.parse_to_dlms_objects()

        assert isinstance(dlms_objects, list)
        assert len(dlms_objects) == 16
        obis_pattern = re.compile(r"(\d+\.){5}\d+")
        for obj in dlms_objects:
            assert isinstance(obj, GXDLMSObject)
            assert re.match(obis_pattern, str(obj.logicalName))

    def test_parse_dlms_to_meter_data(self, unencrypted_valid_data_lg: List[bytes], cosem_config_lg: Cosem):
        parser = prepare_parser(unencrypted_valid_data_lg, cosem_config_lg)
        dlms_objects = parser.parse_to_dlms_objects()
        meter_data = parser.convert_dlms_bundle_to_reader_data(dlms_objects)

        assert isinstance(meter_data, list)
        assert len(meter_data) == 11
        assert any(data.type == MeterDataPointTypes.ACTIVE_POWER_P.value for data in meter_data)
        assert any(data.type == MeterDataPointTypes.ACTIVE_POWER_N.value for data in meter_data)
        assert all(isinstance(data.value, float) for data in meter_data)
        assert all(data.source == "LGZ1030655933512" for data in meter_data)
        assert all(data.timestamp.strftime(r"%m/%d/%y %H:%M:%S") == "07/06/21 14:58:18" for data in meter_data)

    def test_parse_dlms_to_meter_data2(self, unencrypted_valid_data_lg2: List[bytes], cosem_config_lg: Cosem):
        parser = prepare_parser(unencrypted_valid_data_lg2, cosem_config_lg)
        dlms_objects = parser.parse_to_dlms_objects()
        meter_data = parser.convert_dlms_bundle_to_reader_data(dlms_objects)

        assert isinstance(meter_data, list)
        assert len(meter_data) == 8

    def test_ignore_not_parsable_data_to_meter_data(self, unencrypted_invalid_data_lg: List[bytes], cosem_config_lg: Cosem):
        parser = prepare_parser(unencrypted_invalid_data_lg, cosem_config_lg)
        dlms_objects = parser.parse_to_dlms_objects()
        meter_data = parser.convert_dlms_bundle_to_reader_data(dlms_objects)

        assert isinstance(meter_data, list)
        assert len(meter_data) == 5


class TestDlmsParserEncrypted:
    def test_hdlc_to_dlms_objects_without_pushlist(self, encrypted_data_no_pushlist_lg: List[bytes], cosem_config_lg: Cosem):
        parser = prepare_parser(encrypted_data_no_pushlist_lg, cosem_config_lg, "F08660A6C19D2048556BF623AB0257E6")
        dlms_objects = parser.parse_to_dlms_objects()

        assert isinstance(dlms_objects, list)
        assert len(dlms_objects) == 16
        obis_pattern = re.compile(r"(\d+\.){5}\d+")
        for obj in dlms_objects:
            assert isinstance(obj, GXDLMSObject)
            assert re.match(obis_pattern, str(obj.logicalName))
