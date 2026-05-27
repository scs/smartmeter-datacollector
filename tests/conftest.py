#
# Copyright (C) 2024 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
import string
from typing import List, Optional

import pytest

from smartmeter_datacollector.smartmeter.cosem import Cosem
from smartmeter_datacollector.smartmeter.hdlc_dlms_parser import HdlcDlmsParser


def prepare_parser(data: List[bytes], cosem_config: Cosem, cipher_key: Optional[str] = None) -> HdlcDlmsParser:
    parser = HdlcDlmsParser(cosem_config, cipher_key)
    for frame in data:
        parser.append_to_hdlc_buffer(frame)
        parser.extract_data_from_hdlc_frames()
    return parser


@pytest.fixture
def cosem_config_lg() -> Cosem:
    return Cosem(fallback_id="fallback_id")


def split_hex_data_to_frames(meter_data: str) -> List[bytes]:
    bytes_concat = bytes.fromhex(meter_data.translate({ord(c): None for c in string.whitespace}))
    return [b'\x7e\xa0'+frame for frame in bytes_concat.split(b'\x7e\xa0') if frame]
