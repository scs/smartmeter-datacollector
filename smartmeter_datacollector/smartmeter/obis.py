#
# Copyright (C) 2024 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
import re
from dataclasses import dataclass, field
from typing import ClassVar, Union

# 2 (c.d), 3 (c.d.e), 5 (a.b.c.d.e) or 6 (a.b.c.d.e.f) octets; the count is checked in code.
REGEX = r"^\d{1,3}(?:\W\d{1,3}){1,5}$"
REGEX_OCTET = re.compile(r"\d+")


@dataclass(frozen=True)
class OBISCode:
    PATTERN: ClassVar[re.Pattern] = re.compile(REGEX)

    # pylint: disable=invalid-name
    a: int = field(compare=False)
    b: int = field(compare=False)
    c: int
    d: int
    e: int
    f: int = field(default=255, compare=False)

    def __str__(self) -> str:
        return f"{self.a}-{self.b}:{self.c}.{self.d}.{self.e}*{self.f}"

    def to_short_str(self) -> str:
        return f"{self.c}.{self.d}.{self.e}"

    def to_gurux_str(self) -> str:
        return f"{self.a}.{self.b}.{self.c}.{self.d}.{self.e}.{self.f}"

    @classmethod
    def from_string(cls, obis_string: str) -> 'OBISCode':
        """Parse an OBIS string with 2 (c.d, e=0), 3 (c.d.e), 5 (a.b.c.d.e) or 6 (a.b.c.d.e.f) octets."""
        obis_string = obis_string.strip()
        if not cls.PATTERN.match(obis_string):
            raise ValueError(f"Invalid OBIS string {obis_string}.")
        groups = [int(g) for g in REGEX_OCTET.findall(obis_string)]
        if len(groups) in (2, 3):
            return cls(a=1, b=0, c=groups[0], d=groups[1], e=groups[2] if len(groups) == 3 else 0)
        if len(groups) in (5, 6):
            return cls(*groups)
        raise ValueError(f"Invalid OBIS string {obis_string}.")

    @classmethod
    def from_bytes(cls, obis_bytes: Union[bytes, bytearray]) -> 'OBISCode':
        if not cls.is_obis(obis_bytes):
            raise ValueError("Invalid OBIS bytes.")
        return cls(*obis_bytes)

    @staticmethod
    def is_obis(data: Union[bytes, bytearray]) -> bool:
        return (len(data) == 6 and
                data[0] < 10 and
                data[1] <= 64 and
                data[3] < 128)
