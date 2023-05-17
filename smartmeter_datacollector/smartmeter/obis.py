#
# Copyright (C) 2022 Supercomputing Systems AG
# This file is part of smartmeter-datacollector.
#
# SPDX-License-Identifier: GPL-2.0-only
# See LICENSES/README.md for more information.
#
import re
from dataclasses import dataclass, field
from typing import ClassVar, Union

REGEX = r"^(\d{1,3})\W(\d{1,3})\W(\d{1,3})\W(\d{1,3})\W(\d{1,3})\W(\d{1,3})$"


@dataclass(frozen=True)
class OBISCode:
    PATTERN: ClassVar[re.Pattern] = re.compile(REGEX)

    # pylint: disable=invalid-name
    a: int
    b: int = field(compare=False)
    c: int
    d: int
    e: int
    f: int = field(default=255, compare=False)

    def __str__(self) -> str:
        return f"{self.a}-{self.b}:{self.c}.{self.d}.{self.e}*{self.f}"

    def to_gurux_str(self) -> str:
        return f"{self.a}.{self.b}.{self.c}.{self.d}.{self.e}.{self.f}"

    def is_same_type(self, other: 'OBISCode') -> bool:
        """Compares only A, C, D, E parts of an OBIS code."""
        return (self.a == other.a and
                self.b == other.b and
                self.c == other.c and
                self.d == other.d)

    @classmethod
    def from_string(cls, obis_string: str) -> 'OBISCode':
        match = cls.PATTERN.match(obis_string)
        if not match:
            raise ValueError(f"Invalid OBIS string {obis_string}.")
        groups = match.groups()
        return cls(*(int(g) for g in groups))

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
