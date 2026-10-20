#
# Copyright (C) 2026 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
from configparser import ConfigParser

import pytest

from smartmeter_datacollector.smartmeter.adjustments import MeterAdjustments, convert_factor
from smartmeter_datacollector.smartmeter.cosem import Cosem
from smartmeter_datacollector.smartmeter.obis import OBISCode
from smartmeter_datacollector.smartmeter.siemens_td3511 import SiemensParser


def _section(**values):
    parser = ConfigParser()
    parser.read_dict({"reader0": {"type": "lge450", **values}})
    return parser["reader0"]


# --- unit conversion -------------------------------------------------------

def test_convert_factor_prefixes():
    assert convert_factor("W", "kW") == pytest.approx(1e-3)
    assert convert_factor("Wh", "MWh") == pytest.approx(1e-6)
    assert convert_factor("W", "mW") == pytest.approx(1e3)
    assert convert_factor("A", "mA") == pytest.approx(1e3)
    assert convert_factor("V", "kV") == pytest.approx(1e-3)
    assert convert_factor("kW", "W") == pytest.approx(1e3)


def test_convert_factor_reactive_equivalence():
    # var is treated as equivalent to VA (same magnitude, only relabelled)
    assert convert_factor("VA", "var") == pytest.approx(1.0)
    assert convert_factor("VA", "kvar") == pytest.approx(1e-3)
    assert convert_factor("VAh", "kvarh") == pytest.approx(1e-3)


def test_convert_factor_incompatible():
    for a, b in (("W", "V"), ("W", "Wh"), ("Hz", "kHz"), ("W", "banana")):
        with pytest.raises(ValueError):
            convert_factor(a, b)


# --- scaling config --------------------------------------------------------

def test_empty_config_is_noop():
    adj = MeterAdjustments.from_config(_section())
    assert adj.is_noop()


def test_scale_global_and_per_obis():
    adj = MeterAdjustments.from_config(_section(**{"scale": "0.5", "scale.1.0.3.7.0": "2.0"}))
    assert adj.scaling.get_factor(OBISCode(1, 0, 3, 7, 0)) == 2.0
    assert adj.scaling.get_factor(OBISCode(1, 0, 1, 7, 0)) == 0.5


def test_invalid_scale_and_obis_skipped():
    adj = MeterAdjustments.from_config(_section(**{"scale": "x", "scale.bogus": "2"}))
    assert adj.scaling.is_noop()


# --- unit config -----------------------------------------------------------

def test_unit_per_class():
    adj = MeterAdjustments.from_config(_section(**{"unit.W": "kW"}))
    assert adj.units.get_target_unit(OBISCode(1, 0, 1, 7, 0), "W") == "kW"
    # unrelated builtin unit is untouched
    assert adj.units.get_target_unit(OBISCode(1, 0, 32, 7, 0), "V") is None


def test_unit_per_obis_overrides_class():
    adj = MeterAdjustments.from_config(_section(**{"unit.W": "kW", "unit.1.0.1.7.0": "MW"}))
    assert adj.units.get_target_unit(OBISCode(1, 0, 1, 7, 0), "W") == "MW"
    assert adj.units.get_target_unit(OBISCode(1, 0, 21, 7, 0), "W") == "kW"


def test_unit_unknown_class_skipped():
    adj = MeterAdjustments.from_config(_section(**{"unit.banana": "kW"}))
    assert adj.units.is_noop()


# --- resolve (scaling + unit combined) -------------------------------------

def test_resolve_defaults_unchanged():
    adj = MeterAdjustments.from_config(_section())
    scaling, unit = adj.resolve(OBISCode(1, 0, 1, 7, 0), 1.0, "W")
    assert scaling == 1.0
    assert unit == "W"


def test_resolve_unit_conversion_scales_value():
    adj = MeterAdjustments.from_config(_section(**{"unit.W": "kW"}))
    scaling, unit = adj.resolve(OBISCode(1, 0, 1, 7, 0), 1.0, "W")
    assert scaling == pytest.approx(1e-3)
    assert unit == "kW"


def test_resolve_unit_and_scale_compose():
    adj = MeterAdjustments.from_config(_section(**{"scale": "3", "unit.W": "kW"}))
    scaling, unit = adj.resolve(OBISCode(1, 0, 1, 7, 0), 1.0, "W")
    assert scaling == pytest.approx(3 * 1e-3)
    assert unit == "kW"


def test_resolve_incompatible_unit_is_ignored():
    # asking to convert a frequency register to kW must not change anything
    adj = MeterAdjustments.from_config(_section(**{"unit.1.0.14.7.0": "kW"}))
    scaling, unit = adj.resolve(OBISCode(1, 0, 14, 7, 0), 1.0, "Hz")
    assert scaling == 1.0
    assert unit == "Hz"


# --- Cosem integration -----------------------------------------------------

def test_cosem_without_adjustments_keeps_builtin():
    cosem = Cosem(fallback_id="id")
    assert cosem.get_register(OBISCode(1, 0, 31, 7, 0)).scaling == 0.01
    assert cosem.get_register(OBISCode(1, 0, 1, 7, 0)).data_point_type.unit == "W"


def test_cosem_applies_scaling_on_top_of_builtin():
    adj = MeterAdjustments.from_config(_section(scale="2.0"))
    cosem = Cosem(fallback_id="id", adjustments=adj)
    assert cosem.get_register(OBISCode(1, 0, 1, 7, 0)).scaling == 2.0
    assert cosem.get_register(OBISCode(1, 0, 31, 7, 0)).scaling == 0.01 * 2.0


def test_cosem_applies_unit_conversion():
    adj = MeterAdjustments.from_config(_section(**{"unit.W": "kW"}))
    cosem = Cosem(fallback_id="id", adjustments=adj)
    reg = cosem.get_register(OBISCode(1, 0, 1, 7, 0))
    assert reg.data_point_type.unit == "kW"
    assert reg.scaling == pytest.approx(1e-3)


def test_cosem_does_not_mutate_shared_state():
    adj = MeterAdjustments.from_config(_section(**{"scale": "5", "unit.W": "kW"}))
    Cosem(fallback_id="id", adjustments=adj)
    # a fresh, unadjusted Cosem must still see the original built-ins
    fresh = Cosem(fallback_id="id2")
    assert fresh.get_register(OBISCode(1, 0, 31, 7, 0)).scaling == 0.01
    assert fresh.get_register(OBISCode(1, 0, 1, 7, 0)).data_point_type.unit == "W"


# --- Siemens integration ---------------------------------------------------

def test_siemens_applies_unit_and_scaling():
    adj = MeterAdjustments.from_config(_section(**{"unit.W": "kW"}))
    parser = SiemensParser(adjustments=adj)
    # Active power "1.7.0" has a built-in scaling of 1000 and unit W -> kW.
    reg = parser._register_obis["1.7.0"]
    assert reg.data_point_type.unit == "kW"
    assert reg.scaling == pytest.approx(1000 * 1e-3)


def test_siemens_without_adjustments_keeps_builtin():
    parser = SiemensParser()
    assert parser._register_obis["1.7.0"].scaling == 1000
    assert parser._register_obis["1.7.0"].data_point_type.unit == "W"
