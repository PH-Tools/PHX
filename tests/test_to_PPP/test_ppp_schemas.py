# -*- Python Version: 3.10 -*-

"""Tests for PPP schema functions."""

from PHX.to_PPP.ppp_schemas import (
    _pad_num,
    _pad_num_offset,
    _pad_text,
    overbuilt_sections,
)


def test_pad_text():
    result = _pad_text(["a", "b"], 5)
    assert result == ["a", "b", "-", "-", "-"]


def test_pad_num():
    result = _pad_num(["1", "2"], 4)
    assert result == ["1", "2", "", ""]


def test_pad_num_offset():
    result = _pad_num_offset(["1", "2"], 5)
    assert result == ["", "1", "2", "", ""]
    assert len(result) == 5


def test_overbuilt_sections():
    sections = overbuilt_sections()
    assert len(sections) == 5
    assert all(s.rows == 1 and s.cols == 1 for s in sections)
