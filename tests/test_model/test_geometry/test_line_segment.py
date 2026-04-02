# -*- Python Version: 3.10 -*-

"""Tests for PhxLineSegment used in piping and ducting contexts."""

import pytest

from PHX.model.geometry import PhxLineSegment, PhxVertix


def test_line_segment_length(reset_class_counters):
    seg = PhxLineSegment(PhxVertix(0, 0, 0), PhxVertix(3, 4, 0))
    assert seg.length == pytest.approx(5.0)


def test_line_segment_length_3d(reset_class_counters):
    seg = PhxLineSegment(PhxVertix(0, 0, 0), PhxVertix(1, 2, 2))
    assert seg.length == pytest.approx(3.0)


def test_line_segment_zero_length(reset_class_counters):
    seg = PhxLineSegment(PhxVertix(0, 0, 0), PhxVertix(0, 0, 0))
    assert seg.length == pytest.approx(0.0)


def test_line_segment_from_length(reset_class_counters):
    seg = PhxLineSegment.from_length(5.0)
    assert seg.length == pytest.approx(5.0)
    assert seg.vertix_1.x == pytest.approx(0.0)
    assert seg.vertix_2.x == pytest.approx(5.0)


def test_line_segment_from_length_zero(reset_class_counters):
    seg = PhxLineSegment.from_length(0.0)
    assert seg.length == pytest.approx(0.0)


def test_line_segment_equality(reset_class_counters):
    """PhxVertix.__eq__ includes id_num, so shared vertices give equality."""
    v1, v2 = PhxVertix(0, 0, 0), PhxVertix(1, 0, 0)
    seg1 = PhxLineSegment(v1, v2)
    seg2 = PhxLineSegment(v1, v2)
    assert seg1 == seg2


def test_line_segment_equality_reversed(reset_class_counters):
    v1, v2 = PhxVertix(0, 0, 0), PhxVertix(1, 0, 0)
    seg1 = PhxLineSegment(v1, v2)
    seg2 = PhxLineSegment(v2, v1)
    assert seg1 == seg2
