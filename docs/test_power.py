# -*- coding: utf-8 -*-
# -*- Python Version: 2.7 -*-

import pytest
from ph_units.converter import convert, unit_type_dict


def test_W():
    assert convert(1, "W", "KW") == 0.001
    assert convert(1, "W", "W") == 1
    assert convert(1, "W", "BTU/HR") == 3.412141156
    assert convert(1, "W", "KBTU/HR") == 0.003412141


def test_kW():
    assert convert(1, "KW", "KW") == 1
    assert convert(1, "KW", "W") == 1_000
    assert convert(1, "KW", "BTU/HR") == 3412.141156
    assert convert(1, "KW", "KBTU/HR") == 3.412141156


def test_Btu_hr():
    assert convert(1, "BTUH", "W") == 0.293071111
    assert convert(1, "BTUH", "KW") == 0.000293071
    assert convert(650_678, "BTUH", "KW") == 190.694852138


def test_kBtu_aliases():
    assert convert(1, "KBTU/HR", "KW") == 0.293071111
    assert convert(1, "KBTU/H", "KW") == 0.293071111
    assert convert(1, "KBTUHR", "KW") == 0.293071111


def test_kBtu_hr():
    assert convert(1, "KBTUH", "BTUH") == 1_000
    assert convert(1, "KBTUH", "W") == 293.0711111
    assert convert(1, "KBTUH", "KW") == 0.293071111
