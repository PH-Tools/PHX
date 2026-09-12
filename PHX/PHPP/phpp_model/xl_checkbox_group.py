# -*- Python Version: 3.10 -*-

"""A group of mutually exclusive PHPP 'x' check-cells (one selected, siblings cleared)."""

from __future__ import annotations

from collections.abc import Sequence

from PHX.xl import xl_data

# -- 'PHPP_Daten_Ankreuzen' validation is ["", "x"]: None is not a member, so a
# -- cleared sibling is written as "" rather than None.
CHECKED = "x"
UNCHECKED = ""


def checkbox_group_items(sheet_name: str, xl_ranges: Sequence[str], selected_index: int) -> list[xl_data.XlItem]:
    """Return one XlItem per cell in the group: "x" at the selected index, "" at every other.

    PHPP does not flag two ticked boxes in a group; its formulas resolve to whichever
    cell they test first. Clearing the siblings is therefore required, not hygiene.

    Arguments:
    ----------
        * sheet_name (str): The worksheet the group lives on.
        * xl_ranges (Sequence[str]): The group's cell addresses, in order. ie: ["C24", "C30", "C33", "C40"]
        * selected_index (int): The index into 'xl_ranges' of the cell to select.

    Returns:
    --------
        * (list[xl_data.XlItem]): One item per cell in 'xl_ranges'.
    """
    if not 0 <= selected_index < len(xl_ranges):
        raise IndexError(f"Checkbox index {selected_index} is out of range for the group {list(xl_ranges)}.")

    return [
        xl_data.XlItem(sheet_name, xl_range, CHECKED if i == selected_index else UNCHECKED)
        for i, xl_range in enumerate(xl_ranges)
    ]
