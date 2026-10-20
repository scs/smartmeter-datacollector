#
# Copyright (C) 2026 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
"""User-configurable adjustments of meter readings.

Two independent, fully optional adjustments can be configured per reader
section of the ``.ini`` configuration. Both are applied *on top of* the
built-in behaviour, so an empty configuration reproduces exactly the same
values and units as before.

Scaling (multiplicative factor on the numeric value)::

    scale            = 0.5      # factor for every register of the meter
    scale.1.0.3.7.0  = 40       # factor for one OBIS code (overrides `scale`)

Unit conversion (relabel the unit and convert the value accordingly)::

    unit.W           = kW       # convert every register in W to kW
    unit.Wh          = kWh      # convert every register in Wh to kWh
    unit.1.0.3.7.0   = kvar     # convert one OBIS code to a specific unit

Unit conversion and scaling compose: the value emitted for a register is

    raw_value * builtin_scaling * scale_factor(obis) * unit_conversion(obis)

and the emitted unit is the configured target unit (or the built-in unit if
none is configured).
"""
import logging
import re
from dataclasses import dataclass, field
from typing import Dict, Mapping, Optional, Tuple

from smartmeter_datacollector.smartmeter.obis import OBISCode

LOGGER = logging.getLogger("smartmeter")

# --- config keys -----------------------------------------------------------
SCALE_GLOBAL_KEY = "scale"
SCALE_PREFIX = "scale."
UNIT_PREFIX = "unit."

# --- unit handling ---------------------------------------------------------
# Supported SI prefixes and their multiplier relative to the base unit.
SI_PREFIXES: Dict[str, float] = {
    "": 1.0,
    "m": 1e-3,
    "k": 1e3,
    "M": 1e6,
    "G": 1e9,
}
# Longer/unprefixed matches must win, and prefixes are case sensitive
# (``m`` = milli vs ``M`` = mega), so only try the non-empty ones explicitly.
_NON_EMPTY_PREFIXES = [p for p in SI_PREFIXES if p]

# Normalised (upper-case) base units that can be converted, mapping to the
# canonical built-in spelling. ``var``/``varh`` are treated as equivalent to
# ``VA``/``VAh`` so reactive readings can be relabelled to var-style units.
_BASE_ALIASES: Dict[str, str] = {
    "W": "W",
    "WH": "Wh",
    "VA": "VA",
    "VAH": "VAh",
    "VAR": "VA",
    "VARH": "VAh",
    "V": "V",
    "A": "A",
}
# Bare built-in units usable as a per-unit-class selector (`unit.<X> = ...`).
_BUILTIN_UNIT_BY_NORM: Dict[str, str] = {
    "W": "W",
    "WH": "Wh",
    "VA": "VA",
    "VAH": "VAh",
    "V": "V",
    "A": "A",
}

_OBIS_KEY_PATTERN = re.compile(r"^\d[\d\W]*\d$")


def parse_obis(obis_string: str) -> OBISCode:
    """Parse an OBIS code from a config string.

    Accepts the short form ``c.d.e`` (3 groups), the two-octet form ``c.d``
    (``e`` defaults to 0), the five-octet form ``a.b.c.d.e`` and the full
    ``a.b.c.d.e.f``. Any non-word character may be used as a separator.
    ``OBISCode`` equality only considers ``c``, ``d`` and ``e``.
    """
    groups = [int(g) for g in re.split(r"\W+", obis_string.strip()) if g != ""]
    if len(groups) == 2:
        return OBISCode(a=1, b=0, c=groups[0], d=groups[1], e=0)
    if len(groups) == 3:
        return OBISCode(a=1, b=0, c=groups[0], d=groups[1], e=groups[2])
    if len(groups) in (5, 6):
        return OBISCode(*groups)
    raise ValueError(f"Invalid OBIS string '{obis_string}'.")


def _split_unit(unit: str) -> Tuple[float, str]:
    """Split a unit into (prefix multiplier, canonical base unit).

    Raises ``ValueError`` if the base unit is unknown / not convertible.
    """
    for prefix in _NON_EMPTY_PREFIXES:
        if unit.startswith(prefix):
            rest = unit[len(prefix):]
            base = _BASE_ALIASES.get(rest.upper())
            if base is not None:
                return SI_PREFIXES[prefix], base
    base = _BASE_ALIASES.get(unit.upper())
    if base is not None:
        return 1.0, base
    raise ValueError(f"Unknown or non-convertible unit '{unit}'.")


def convert_factor(from_unit: str, to_unit: str) -> float:
    """Return the factor to convert a value from ``from_unit`` to ``to_unit``.

    Both units must share the same base quantity (e.g. ``W`` -> ``kW``).
    Raises ``ValueError`` for incompatible or unknown units.
    """
    from_mult, from_base = _split_unit(from_unit)
    to_mult, to_base = _split_unit(to_unit)
    if from_base != to_base:
        raise ValueError(f"Cannot convert '{from_unit}' to '{to_unit}': incompatible units.")
    return from_mult / to_mult


@dataclass
class ScalingConfig:
    """User-defined multiplicative scaling for a single meter."""
    factor: float = 1.0
    per_obis: Dict[OBISCode, float] = field(default_factory=dict)

    def get_factor(self, obis: OBISCode) -> float:
        """Extra factor for ``obis`` (per-OBIS wins over the global factor)."""
        return self.per_obis.get(obis, self.factor)

    def is_noop(self) -> bool:
        return self.factor == 1.0 and not self.per_obis


@dataclass
class UnitConfig:
    """User-defined unit overrides for a single meter."""
    # Target unit keyed by the *built-in* unit it replaces (e.g. "W" -> "kW").
    per_unit: Dict[str, str] = field(default_factory=dict)
    # Target unit keyed by a specific OBIS code (overrides ``per_unit``).
    per_obis: Dict[OBISCode, str] = field(default_factory=dict)

    def get_target_unit(self, obis: OBISCode, builtin_unit: str) -> Optional[str]:
        """Return the configured target unit for a register, or ``None``."""
        if obis in self.per_obis:
            return self.per_obis[obis]
        return self.per_unit.get(builtin_unit)

    def is_noop(self) -> bool:
        return not self.per_unit and not self.per_obis


@dataclass
class MeterAdjustments:
    """All user-configured adjustments for a single meter."""
    scaling: ScalingConfig = field(default_factory=ScalingConfig)
    units: UnitConfig = field(default_factory=UnitConfig)

    def is_noop(self) -> bool:
        return self.scaling.is_noop() and self.units.is_noop()

    def resolve(self, obis: OBISCode, builtin_scaling: float, builtin_unit: str) -> Tuple[float, str]:
        """Resolve the effective (scaling, unit) for a register.

        Returns the final scaling factor (built-in scaling multiplied by the
        user factor and any unit-conversion factor) and the final unit label.
        Invalid/incompatible unit conversions are logged and ignored so a
        typo never crashes the collector and never silently drops the reading.
        """
        scaling = builtin_scaling * self.scaling.get_factor(obis)
        unit = builtin_unit
        target = self.units.get_target_unit(obis, builtin_unit)
        if target and target != builtin_unit:
            try:
                scaling *= convert_factor(builtin_unit, target)
                unit = target
            except ValueError as ex:
                LOGGER.warning("Ignoring unit override for OBIS %s: %s", obis, ex)
        return scaling, unit

    @classmethod
    def from_config(cls, section: Mapping[str, str]) -> "MeterAdjustments":
        """Build a ``MeterAdjustments`` from a reader config section."""
        scaling = ScalingConfig()
        units = UnitConfig()
        for raw_key, raw_value in section.items():
            key = raw_key.strip().lower()
            if key == SCALE_GLOBAL_KEY:
                factor = MeterAdjustments._parse_factor(key, raw_value)
                if factor is not None:
                    scaling.factor = factor
            elif key.startswith(SCALE_PREFIX):
                MeterAdjustments._parse_scale_per_obis(key[len(SCALE_PREFIX):], key, raw_value, scaling)
            elif key.startswith(UNIT_PREFIX):
                MeterAdjustments._parse_unit(key[len(UNIT_PREFIX):], raw_value, units)
        return cls(scaling=scaling, units=units)

    @staticmethod
    def _parse_scale_per_obis(selector: str, key: str, raw_value: str, scaling: ScalingConfig) -> None:
        factor = MeterAdjustments._parse_factor(key, raw_value)
        if factor is None:
            return
        try:
            scaling.per_obis[parse_obis(selector)] = factor
        except ValueError:
            LOGGER.warning("Ignoring scaling for invalid OBIS '%s'.", selector)

    @staticmethod
    def _parse_unit(selector: str, raw_value: str, units: UnitConfig) -> None:
        target = raw_value.strip()
        if not target:
            return
        if _OBIS_KEY_PATTERN.match(selector):
            try:
                units.per_obis[parse_obis(selector)] = target
            except ValueError:
                LOGGER.warning("Ignoring unit override for invalid OBIS '%s'.", selector)
            return
        builtin = _BUILTIN_UNIT_BY_NORM.get(selector.upper())
        if builtin is None:
            LOGGER.warning("Ignoring unit override for unknown unit class '%s'.", selector)
            return
        units.per_unit[builtin] = target

    @staticmethod
    def _parse_factor(key: str, raw_value: str) -> Optional[float]:
        try:
            return float(raw_value)
        except (TypeError, ValueError):
            LOGGER.warning("Ignoring invalid scaling factor '%s' for '%s'.", raw_value, key)
            return None
