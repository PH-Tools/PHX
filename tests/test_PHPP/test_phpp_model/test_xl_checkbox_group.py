# -*- Python Version: 3.10 -*-

"""Tests for the mutually exclusive PHPP 'x' check-cell group."""

import pytest

from PHX.PHPP.phpp_model.xl_checkbox_group import checkbox_group_items

RANGES = ["C24", "C30", "C33", "C40"]


def _states(items) -> dict[str, str]:
    return {item.xl_range: item.write_value for item in items}


@pytest.mark.parametrize(
    "index, expected",
    [
        (0, {"C24": "x", "C30": "", "C33": "", "C40": ""}),
        (2, {"C24": "", "C30": "", "C33": "x", "C40": ""}),
        (3, {"C24": "", "C30": "", "C33": "", "C40": "x"}),
    ],
    ids=["first", "middle", "last"],
)
def test_selects_one_cell_and_clears_every_sibling(index, expected):
    items = checkbox_group_items("Ground", RANGES, index)

    assert _states(items) == expected
    assert {item.sheet_name for item in items} == {"Ground"}


@pytest.mark.parametrize("index", [-1, 4])
def test_out_of_range_index_raises(index):
    with pytest.raises(IndexError):
        checkbox_group_items("Ground", RANGES, index)
