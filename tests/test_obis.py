#
# Copyright (C) 2024 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
import pytest

from smartmeter_datacollector.smartmeter.obis import OBISCode


def test_create_from_gurux_string():
    obis_string = "1.0.1.7.0.255"
    obis = OBISCode.from_string(obis_string)
    assert obis
    assert obis.a == 1
    assert obis.b == 0
    assert obis.c == 1
    assert obis.d == 7
    assert obis.e == 0
    assert obis.f == 255


def test_create_from_IEC_62056_string():
    obis_string = "1-0:1.7.0*255"
    obis = OBISCode.from_string(obis_string)
    assert obis
    assert obis.a == 1
    assert obis.b == 0
    assert obis.c == 1
    assert obis.d == 7
    assert obis.e == 0
    assert obis.f == 255


def test_create_from_short_string():
    obis_string = "1.7.0"
    obis = OBISCode.from_string(obis_string)
    assert obis
    assert obis.a == 1
    assert obis.b == 0
    assert obis.c == 1
    assert obis.d == 7
    assert obis.e == 0
    assert obis.f == 255


def test_create_from_string_all_forms():
    assert OBISCode.from_string("3.7.0") == OBISCode(1, 0, 3, 7, 0)
    assert OBISCode.from_string("14.7") == OBISCode(1, 0, 14, 7, 0)
    assert OBISCode.from_string("1.0.3.7.0") == OBISCode(1, 0, 3, 7, 0)
    assert OBISCode.from_string("1.0.3.7.0.255") == OBISCode(1, 0, 3, 7, 0)


def test_create_from_short_string_two_octets():
    obis = OBISCode.from_string("14.7")
    assert (obis.a, obis.b, obis.c, obis.d, obis.e, obis.f) == (1, 0, 14, 7, 0, 255)


@pytest.mark.parametrize("bad", ["", "1", "1.2.3.4", "1.2.3.4.5.6.7", "not.an.obis"])
def test_invalid_strings(bad):
    with pytest.raises(ValueError):
        OBISCode.from_string(bad)


def test_create_from_bytes():
    obis_bytes = bytes.fromhex("01 01 01 08 02 FF")
    obis = OBISCode.from_bytes(obis_bytes)
    assert obis
    assert obis.a == 1
    assert obis.b == 1
    assert obis.c == 1
    assert obis.d == 8
    assert obis.e == 2
    assert obis.f == 255


def test_to_IEC62056_string():
    obis = OBISCode(1, 0, 1, 7, 0, 255)
    assert str(obis) == "1-0:1.7.0*255"


def test_to_gurux_string():
    obis = OBISCode(1, 0, 1, 7, 0, 255)
    assert obis.to_gurux_str() == "1.0.1.7.0.255"


def test_to_short_string():
    obis = OBISCode(1, 0, 1, 7, 0, 255)
    assert obis.to_short_str() == "1.7.0"


def test_only_compare_relevant_octets():
    obis = OBISCode(1, 0, 1, 7, 0, 255)
    assert obis == OBISCode(1, 1, 1, 7, 0, 255)
    assert obis == OBISCode(1, 0, 1, 7, 0, 128)
    assert obis == OBISCode(0, 0, 1, 7, 0, 255)
    assert obis != OBISCode(1, 0, 2, 7, 0, 255)
    assert obis != OBISCode(1, 0, 1, 16, 0, 255)
    assert obis != OBISCode(1, 0, 1, 7, 1, 255)


def test_hash_of_obis():
    obis = OBISCode(1, 0, 1, 7, 0, 255)
    obis_diff = OBISCode(1, 0, 2, 7, 0, 255)
    obis_same = OBISCode(1, 2, 1, 7, 0, 255)

    assert hash(obis) == hash(obis_same)
    assert hash(obis) != hash(obis_diff)
