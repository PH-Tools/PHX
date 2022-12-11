# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Exceptions used by the IO classes."""


class FindSectionMarkerException(Exception):
    """Raises when the IO controller cannot find the reference marker in a column."""

    def __init__(self, search_string, _sheet_name, _col_letter):
        self.msg = (
            f"\n\tError: Cannot find the the marker: '{search_string}' "
            f"in the worksheet '{_sheet_name}' column '{_col_letter}'?"
        )
        super().__init__(self.msg)
