# -*- Python Version: 3.10 -*-

"""Controller Class for the PHPP "Ground" worksheet."""

from __future__ import annotations

from PHX.PHPP.phpp_localization import shape_model
from PHX.PHPP.phpp_model import ground_data
from PHX.PHPP.sheet_io.io_exceptions import FindSectionMarkerException
from PHX.xl import xl_app


class Ground:
    """IO Controller for the PHPP "Ground" worksheet."""

    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.Ground):
        self.xl = _xl
        self.shape = _shape

    def find_section_header_row(self, _row_start: int = 1, _row_end: int = 100) -> int:
        """Return the row number of the 'Floor slab type' header, which every input row is offset from."""
        if not (block := self.shape.input_block):
            raise ground_data.GroundExportError(f"The '{self.shape.name}' worksheet layout is not mapped.")

        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.shape.name,
            _col=block.locator_col_header,
            _row_start=_row_start,
            _row_end=_row_end,
        )

        # -- The data begins at '_row_start', so enumerate from there: the
        # -- caller wants a worksheet row number, not an index into the block.
        for i, val in enumerate(xl_data, start=_row_start):
            if block.locator_string_header == val:
                return i

        raise FindSectionMarkerException(block.locator_string_header, self.shape.name, block.locator_col_header)

    def write_foundation(self, _foundation_block: ground_data.GroundFoundationBlock) -> None:
        """Write one foundation into building section 1."""
        for xl_item in _foundation_block.create_xl_items(self.shape.name, self.find_section_header_row()):
            self.xl.write_xl_item(xl_item)
