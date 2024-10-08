#
# Copyright (C) 2024 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
from typing import List, Optional

import pytest

from smartmeter_datacollector.smartmeter.cosem import Cosem, RegisterCosem
from smartmeter_datacollector.smartmeter.hdlc_dlms_parser import HdlcDlmsParser
from smartmeter_datacollector.smartmeter.meter_data import MeterDataPointTypes
from smartmeter_datacollector.smartmeter.obis import OBISCode


def prepare_parser(data: List[bytes], cosem_config: Cosem, cipher_key: Optional[str] = None) -> HdlcDlmsParser:
    parser = HdlcDlmsParser(cosem_config, cipher_key)
    for frame in data:
        parser.append_to_hdlc_buffer(frame)
        parser.extract_data_from_hdlc_frames()
    return parser


@pytest.fixture
def cosem_config_lg() -> Cosem:
    return Cosem(fallback_id="fallback_id")


@pytest.fixture
def unencrypted_valid_data_lg() -> List[bytes]:
    data_str: List[str] = []
    data_str.append("7E A0 84 CE FF 03 13 12 8B E6 E7 00 E0 40 00 01 00 00 70 0F 00 00 CB C2 0C 07 E5 07 06 02 0E 3A 05 FF 80 00 00 02 10 01 10 02 04 12 00 28 09 06 00 08 19 09 00 FF 0F 02 12 00 00 02 04 12 00 28 09 06 00 08 19 09 00 FF 0F 01 12 00 00 02 04 12 00 01 09 06 00 00 2A 00 00 FF 0F 02 12 00 00 02 04 12 00 01 09 06 00 00 60 01 01 FF 0F 02 12 00 00 02 04 12 00 08 09 06 00 00 01 00 00 FF 0F 02 12 00 00 77 C8 7E")
    data_str.append("7E A0 7D CE FF 03 13 D0 45 E0 40 00 02 00 00 6C 02 04 12 00 03 09 06 01 00 01 07 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 00 02 07 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 00 03 07 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 00 04 07 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 01 08 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 02 08 00 FF 0F 02 12 00 00 B3 98 7E")
    data_str.append("7E A0 84 CE FF 03 13 12 8B E6 E7 00 E0 40 00 01 00 00 70 0F 00 00 CB C6 0C 07 E5 07 06 02 0E 3A 10 FF 80 00 00 02 10 01 10 02 04 12 00 28 09 06 00 08 19 09 00 FF 0F 02 12 00 00 02 04 12 00 28 09 06 00 08 19 09 00 FF 0F 01 12 00 00 02 04 12 00 01 09 06 00 00 2A 00 00 FF 0F 02 12 00 00 02 04 12 00 01 09 06 00 00 60 01 01 FF 0F 02 12 00 00 02 04 12 00 08 09 06 00 00 01 00 00 FF 0F 02 12 00 00 27 73 7E")
    data_str.append("7E A0 7D CE FF 03 13 D0 45 E0 40 00 02 00 00 6C 02 04 12 00 03 09 06 01 00 01 07 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 00 02 07 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 00 03 07 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 00 04 07 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 01 08 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 02 08 00 FF 0F 02 12 00 00 B3 98 7E")
    data_str.append("7E A0 8B CE FF 03 13 EE E1 E0 40 00 03 00 00 7A 02 04 12 00 03 09 06 01 01 05 08 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 06 08 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 07 08 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 08 08 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 00 0D 07 00 FF 0F 02 12 00 00 09 06 00 08 19 09 00 FF 09 10 4C 47 5A 31 30 33 30 36 35 35 39 33 33 35 31 32 09 07 31 39 33 35 3B 2A 7E")
    data_str.append("7E A0 57 CE FF 03 13 E9 69 E0 C0 00 04 00 00 46 39 31 32 09 0C 07 E5 07 06 02 0E 3A 12 FF 80 00 81 06 00 00 00 1C 06 00 00 00 00 06 00 00 00 00 06 00 00 00 0A 06 00 0D 88 C1 06 00 00 00 00 06 00 00 00 12 06 00 00 00 01 06 00 00 00 00 06 00 04 72 0D 12 03 AD C2 CE 7E")
    data = list(map(lambda frag: bytes.fromhex(frag.replace(" ", "")), data_str))
    return data


@pytest.fixture
def unencrypted_invalid_data_lg() -> List[bytes]:
    data_str: List[str] = []
    data_str.append("7E A0 84 CE FF 03 13 12 8B E6 E7 00 E0 40 00 01 00 00 70 0F 00 00 C9 60 0C 07 E5 07 06 02 0E 07 37 FF 80 00 00 02 10 01 10 02 04 12 00 28 09 06 00 08 19 09 00 FF 0F 02 12 00 00 02 04 12 00 28 09 06 00 08 19 09 00 FF 0F 01 12 00 00 02 04 12 00 01 09 06 00 00 2A 00 00 FF 0F 02 12 00 00 02 04 12 00 01 09 06 00 00 60 01 01 FF 0F 02 12 00 00 02 04 12 00 08 09 06 00 00 01 00 00 FF 0F 02 12 00 00 35 37 7E")
    data_str.append("7E A0 7D CE FF 03 13 D0 45 E0 40 00 02 00 00 6C 02 04 12 00 03 09 06 01 00 01 07 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 00 02 07 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 00 03 07 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 00 04 07 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 01 08 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 02 08 00 FF 0F 02 12 00 00 B3 98 7E")
    data_str.append("7E A0 7D CE FF 03 13 D0 45 E0 40 00 02 00 00 6C 02 04 12 00 03 09 06 01 00 01 07 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 00 02 07 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 00 03 07 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 00 04 07 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 01 08 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 02 08 00 FF 0F 02 12 00 00 B3 98 7E")
    data_str.append("7E A0 8B CE FF 03 13 EE E1 E0 40 00 03 00 00 7A 02 04 12 00 03 09 06 01 01 05 08 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 06 08 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 07 08 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 08 08 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 00 0D 07 00 FF 0F 02 12 00 00 09 06 00 08 19 09 00 FF 09 10 4C 47 5A 31 30 33 30 36 35 35 39 33 33 35 31 32 09 07 31 39 33 35 3B 2A 7E")
    data_str.append("7E A0 57 CE FF 03 13 E9 69 E0 C0 00 04 00 00 46 39 31 32 09 0C 07 E5 07 06 02 0E 08 13 FF 80 00 81 06 00 00 00 00 06 00 00 00 00 06 00 00 00 00 06 00 00 00 00 06 00 0D 88 C1 06 00 00 00 00 06 00 00 00 12 06 00 00 00 01 06 00 00 00 00 06 00 04 72 0D 12 03 E8 AD 29 7E")
    data = list(map(lambda frag: bytes.fromhex(frag.replace(" ", "")), data_str))
    return data


@pytest.fixture
def unencrypted_valid_data_lg2() -> List[bytes]:
    data_str: List[str] = []
    data_str.append("7E A0 84 CE FF 03 13 12 8B E6 E7 00 E0 40 00 01 00 00 70 0F 00 03 B5 33 0C 07 E6 0B 16 02 10 25 1E FF 80 00 00 02 0B 01 0B 02 04 12 00 28 09 06 00 08 19 09 00 FF 0F 02 12 00 00 02 04 12 00 28 09 06 00 08 19 09 00 FF 0F 01 12 00 00 02 04 12 00 01 09 06 00 00 60 01 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 00 01 07 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 00 02 07 00 FF 0F 02 12 00 00 4C 21 7E")
    data_str.append("7E A0 8B CE FF 03 13 EE E1 E0 40 00 02 00 00 7A 02 04 12 00 03 09 06 01 01 01 08 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 02 08 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 05 08 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 06 08 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 07 08 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 08 08 00 FF 0F 02 12 00 00 09 06 00 08 19 09 00 FF 09 08 34 34 33 33 8B 52 7E")
    data_str.append("7E A0 3D CE FF 03 13 F2 84 E0 C0 00 03 00 00 2C 37 38 31 31 06 00 00 03 09 06 00 00 00 00 06 01 7F BF EB 06 00 43 7A DE 06 00 2F CD AE 06 00 00 33 BF 06 00 37 70 2E 06 00 F0 41 58 40 EF 7E")
    data = list(map(lambda frag: bytes.fromhex(frag.replace(" ", "")), data_str))
    return data


@pytest.fixture
def unencrypted_valid_data_iskra() -> List[bytes]:
    data_str: List[str] = []
    data_str.append("7E A8 A4 CF 02 23 03 99 96 E6 E7 00 0F 00 00 04 33 0C 07 E4 08 0F 06 06 13 2D 00 FF 88 80 02 1C 01 1C 02 04 12 00 28 09 06 00 06 19 09 00 FF 0F 02 12 00 00 02 04 12 00 28 09 06 00 06 19 09 00 FF 0F 01 12 00 00 02 04 12 00 01 09 06 00 00 2A 00 00 FF 0F 02 12 00 00 02 04 12 00 01 09 06 00 00 60 01 01 FF 0F 02 12 00 00 02 04 12 00 08 09 06 00 00 01 00 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 01 07 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 02 07 00 FF 0F 02 12 00 00 02 04 12 37 4F 7E")
    data_str.append("7E A8 A4 CF 02 23 03 99 96 00 03 09 06 01 01 03 07 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 04 07 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 01 08 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 01 08 01 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 01 08 02 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 02 08 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 02 08 01 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 02 08 02 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 05 08 00 FF 00 00 7E")
    data_str.append("7E A8 A4 CF 02 23 03 99 96 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 05 08 01 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 05 08 02 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 06 08 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 06 08 01 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 06 08 02 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 07 08 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 07 08 01 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 07 08 02 FF 0F 02 12 00 00 02 04 12 00 03 B2 E4 7E")
    data_str.append("7E A8 A4 CF 02 23 03 99 96 09 06 01 01 08 08 00 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 08 08 01 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 01 08 08 02 FF 0F 02 12 00 00 02 04 12 00 03 09 06 01 00 0D 07 00 FF 0F 02 12 00 00 09 06 00 06 19 09 00 FF 09 10 49 53 4B 31 30 33 30 37 37 35 32 31 33 38 35 39 09 07 31 38 37 36 33 35 30 09 0C 07 E4 08 0F 06 06 13 2D 00 FF 88 80 06 00 00 00 00 06 00 00 00 00 06 00 00 00 00 06 00 00 00 00 06 00 5F 0E A5 06 00 2F 44 2F 06 00 2F CA 76 06 00 00 BE FE 7E")
    data_str.append("7E A0 55 CF 02 23 13 A2 33 00 00 06 00 00 00 00 06 00 00 00 00 06 00 05 47 7C 06 00 03 84 3F 06 00 01 C3 3D 06 00 00 00 09 06 00 00 00 09 06 00 00 00 00 06 00 00 00 00 06 00 00 00 00 06 00 00 00 00 06 00 01 0A F7 06 00 00 94 B0 06 00 00 76 47 12 00 00 12 7B 7E")
    data = list(map(lambda frag: bytes.fromhex(frag.replace(" ", "")), data_str))
    return data


@pytest.fixture
def encrypted_valid_data_lge570() -> List[bytes]:
    data_str: List[str] = []
    data_str.append("7E A0 88 CE 9B 03 13 0E 9A E6 E7 00 E0 40 00 01 00 00 74 DB 08 4C 47 5A 67 74 20 62 95 82 01 FF 20 00 00 24 76 2F 13 88 34 08 13 B4 C9 27 EC 19 C3 9F A9 36 B6 F7 A3 FE 6F 63 CE 15 5C 0B E7 58 5D 3E AE 76 2C 0E 39 1A E4 AC BA 9D 9C 24 00 F8 72 57 CA 7C 28 46 02 71 36 FF 19 77 8B AB AC 6B 0C 56 80 21 EB 2E E5 DF DA 3C 39 BC 28 09 2D 6C 3B 32 E8 D3 3B 63 EC E8 93 D9 C3 D4 23 A4 42 00 D9 DB 27 10 0E 9B 32 E7 C2 7E")
    data_str.append("7E A0 85 CE 9B 03 13 7A E6 E0 40 00 02 00 00 74 23 D8 DA F9 65 DC DC 8F 3A 42 CD D8 2C D3 1E FF B9 89 FF 60 7C E6 4D 8B 34 85 7A B2 86 3E 80 49 C8 E2 AC A0 59 86 ED 6C D5 3A 83 71 CC 85 01 1D 4E 63 24 51 31 C6 76 07 F2 5A 62 39 B0 58 46 B2 7B 79 00 70 33 A3 97 AB 21 A6 5B 34 30 8C 53 58 B9 D9 22 4A E4 A1 17 9D B1 77 13 B3 2C 2D 42 3A 0C 87 60 4F 0A F9 DA DE AF F6 DE E1 C1 4E 0C AF 8A 53 A3 B7 88 DA 7E")
    data_str.append("7E A0 85 CE 9B 03 13 7A E6 E0 40 00 03 00 00 74 2B CF 7B 29 B7 D2 E5 71 FF F8 BC 97 C9 83 A8 E0 6A C7 C1 F4 2D C7 C5 A8 90 E4 24 C6 55 C5 68 8C 89 F5 B3 47 D5 D3 87 FF 3A 37 58 AF F8 D4 FD 2E 6E 23 BC 92 B3 18 EB 26 69 16 AF 1E 03 F4 DC B6 E1 59 AB 46 8C C4 7A 27 34 E0 A5 5E B3 26 F3 EF 3B 45 83 B3 13 8E 72 D3 FD BA 36 EB CC 35 C7 37 5B A8 5E 67 BB C9 50 ED 07 7E B3 83 F9 8C 71 1C 14 64 AC 23 22 C1 7E")
    data_str.append("7E A0 85 CE 9B 03 13 7A E6 E0 40 00 04 00 00 74 D6 61 A7 B9 C0 68 C6 75 D0 43 A5 A1 0A 63 F9 7A 38 D1 8D BF 5C 0C 5E 1E E0 10 7B F5 04 89 3E 59 B9 05 47 92 29 13 D4 FE BC 0D 49 28 C0 16 AB 3B BA 94 5E 88 AF 9C 0F B0 4B D0 57 FB 9C D8 10 8E DE 20 F9 F5 A9 5A 2E 65 14 BF 93 AE 0C 8E EA F3 70 39 9A 8D EF 06 52 A4 77 C5 C6 48 2B 4C 99 16 37 28 ED 40 61 F9 3B F5 6E 3F BE 6E AF 05 09 EE 6E 0A 05 6B 17 0C 7E")
    data_str.append("7E A0 4D CE 9B 03 13 2D F7 E0 C0 00 05 00 00 3C 41 AE 08 9D A2 FC BA 2E E3 CF 47 2D C8 E3 B5 E6 DB BA BF C5 20 ED E1 F1 3C 54 13 EC 0D A8 B0 D3 96 D7 35 4B 5C 7E E8 2F 9C BA 12 5F 80 B9 C9 38 0C F5 DD 9D 4E 16 48 C3 35 01 FE F3 6E 0F 7E")
    data = list(map(lambda frag: bytes.fromhex(frag.replace(" ", "")), data_str))
    return data


@pytest.fixture
def encrypted_data_no_pushlist_lg() -> List[bytes]:
    data_str: List[str] = []
    data_str.append("7E A0 8B CE FF 03 13 EE E1 E6 E7 00 E0 40 00 01 00 00 77 DB 08 4C 47 5A 67 73 78 1F D0 82 01 03 30 00 06 90 3C EB 7B E1 75 48 BF D7 C3 6E DF 96 48 93 7D 7C 78 26 2B E5 FC FE E3 6B 41 D0 61 CF F3 FA 3A E6 91 8B FD C6 1F 95 67 19 E2 95 91 FC D6 D0 A1 98 D6 CA 49 CC DD 56 5F D3 8A 5F 9A 6C 8E AC 3A BE EE 11 0D 2E C4 EB B6 DC 10 43 D3 5A 8B C8 7D 42 0E 75 A2 3C 44 F4 08 B7 A7 31 F1 62 1F 84 86 F3 50 C3 A4 9D 02 06 B1 3A 7E")
    data_str.append("7E A0 8B CE FF 03 13 EE E1 E0 40 00 02 00 00 7A 48 44 3E 98 6B 54 C0 4A 4E 84 AE 52 EC F1 89 4A CC 58 67 52 28 E2 45 6F 9B ED CD 22 79 03 FE 91 16 50 5C 90 02 A6 9A C4 5E F7 35 40 9B 4D 7E CE 2D 89 CD 86 F6 5B FB DF E6 1C 94 3F CE A4 CA 64 6C 3E EC BD 8C 38 BA 05 7B C5 21 DA 2C 08 E5 9B E8 FB B3 FE 59 27 94 D5 80 41 AF 33 2D C0 ED 7A 51 19 06 ED A5 24 07 95 81 9C 85 39 68 52 D7 9D 3A B7 B8 3B C7 30 23 F7 4B 5F 01 FE 7E")
    data_str.append(
        "7E A0 30 CE FF 03 13 86 F8 E0 C0 00 03 00 00 1F 1F FE C7 27 11 0F 74 B7 EF F4 1B 48 F7 47 B6 B6 A2 39 5B 42 BD 61 EA 18 7E D9 A0 99 8B 81 45 44 78 7E")
    data = list(map(lambda frag: bytes.fromhex(frag.replace(" ", "")), data_str))
    return data


@pytest.fixture
def unencrypted_extended_register_data() -> List[bytes]:
    data_str: List[str] = []
    data_str.append("7E A0 84 CE FF 03 13 12 8B E6 E7 00 E0 40 00 01 00 00 70 0F 00 04 15 7A 0C 07 E8 06 0B 02 10 00 00 FF 80 00 00 02 0A 01 0A 02 04 12 00 28 09 06 00 0B 19 09 00 FF 0F 02 12 00 00 02 04 12 00 28 09 06 00 0B 19 09 00 FF 0F 01 12 00 00 02 04 12 00 01 09 06 00 01 60 01 00 FF 0F 02 12 00 00 02 04 12 00 01 09 06 00 02 60 01 00 FF 0F 02 12 00 00 02 04 12 00 01 09 06 00 03 60 01 00 FF 0F 02 12 00 00 EB F5 7E")
    data_str.append("7E A0 86 CE FF 03 13 9A 9D E0 40 00 02 00 00 75 02 04 12 00 01 09 06 00 04 60 01 00 FF 0F 02 12 00 00 02 04 12 00 04 09 06 00 01 18 02 01 FF 0F 02 12 00 00 02 04 12 00 04 09 06 00 02 18 02 01 FF 0F 02 12 00 00 02 04 12 00 04 09 06 00 03 18 02 01 FF 0F 02 12 00 00 02 04 12 00 04 09 06 00 04 18 02 01 FF 0F 02 12 00 00 09 06 00 0B 19 09 00 FF 09 08 32 34 35 32 31 36 36 32 09 01 00 09 01 00 09 01 00 C4 FD 7E")
    data_str.append("7E A0 25 CE FF 03 13 92 6A E0 C0 00 03 00 00 14 05 00 00 77 51 05 00 00 00 00 05 00 00 00 00 05 00 00 00 00 87 59 7E")
    data = list(map(lambda frag: bytes.fromhex(frag.replace(" ", "")), data_str))
    return data
