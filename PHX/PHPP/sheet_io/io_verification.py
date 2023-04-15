# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Controller Class for the PHPP Climate worksheet."""

from __future__ import annotations
from dataclasses import dataclass
from typing import List

from PHX.xl import xl_app
from PHX.PHPP.phpp_localization import shape_model
from PHX.PHPP.phpp_model import verification_data


class VerificationInputLocation:
    """Generic input item for Verification worksheet items."""

    def __init__(
        self,
        _xl: xl_app.XLConnection,
        _sheet_name: str,
        _search_col: str,
        _search_item: str,
        _input_row_offset: int,
    ):
        self.xl = _xl
        self.sheet_name = _sheet_name
        self.search_col = _search_col
        self.search_item = _search_item
        self.input_row_offset = _input_row_offset

    def find_input_row(self, _row_start: int = 1, _row_end: int = 200) -> int:
        """Return the row number where the search-item is found input."""
        xl_data = self.xl.get_single_column_data(
            _sheet_name=self.sheet_name,
            _col=self.search_col,
            _row_start=_row_start,
            _row_end=_row_end,
        )

        for i, val in enumerate(xl_data, start=_row_start):
            if self.search_item in str(val):
                return i + self.input_row_offset

        raise Exception(
            f'\n\tError: Not able to find the "{self.search_item}" input '
            f'section of the "{self.sheet_name}" worksheet? Please be sure '
            f'the item is note with the "{self.search_item}" flag in column {self.search_col}?'
        )


@dataclass
class TeamMemberData:
    """A Dataclass to store team-member information when read in from the PHPP."""

    name: str
    street_name: str
    post_code: str
    city: str
    state: str
    country: str

    @classmethod
    def from_raw_excel_data(cls, _xl_data) -> TeamMemberData:
        """Create a new TeamMemberData object from raw excel data read in from PHPP

        Arguments:
        ----------
            * _xl_data: List[List[str]]: A list of lists containing the data read
                in from PHPP.
        Returns:
        --------
            * (TeamMemberData): A new TeamMemberData object with the values from the
                input data set.
        """
        try:
            return cls(
                name=_xl_data[0][0],
                street_name=_xl_data[1][0],
                post_code=_xl_data[2][0],
                city=_xl_data[2][1],
                state=_xl_data[3][0],
                country=_xl_data[3][2],
            )
        except:
            msg = f"Error reading in Team Member Data from the PHPP? Got:\n{_xl_data}"
            raise Exception(msg)


class Verification:
    def __init__(self, _xl: xl_app.XLConnection, _shape: shape_model.Verification):
        self.xl = _xl
        self.shape = _shape

    def _create_input_location_object(
        self, _phpp_model_obj: verification_data.VerificationInput
    ) -> VerificationInputLocation:
        """Create and setup the VerificationInputLocation object with the correct data."""
        phpp_obj_shape: shape_model.VerificationInputItem = getattr(
            self.shape, _phpp_model_obj.input_type
        )
        return VerificationInputLocation(
            _xl=self.xl,
            _sheet_name=self.shape.name,
            _search_col=phpp_obj_shape.locator_col,
            _search_item=phpp_obj_shape.locator_string,
            _input_row_offset=phpp_obj_shape.input_row_offset,
        )

    def write_item(self, _phpp_model_obj: verification_data.VerificationInput) -> None:
        """Write the VerificationInputItem item out to the PHPP Verification Worksheet."""
        input_object = self._create_input_location_object(_phpp_model_obj)
        input_row = input_object.find_input_row()
        xl_item = _phpp_model_obj.create_xl_item(self.shape.name, input_row)
        self.xl.write_xl_item(xl_item)

    def read_architect(self) -> TeamMemberData:
        """Return a TeamMemberData object with the architect info from PHPP."""
        data = self.xl.get_data(self.shape.name, "F18:H21")
        return TeamMemberData.from_raw_excel_data(data)

    def read_energy_consultant(self) -> TeamMemberData:
        """Return a TeamMemberData object with the consultant info from PHPP."""
        data = self.xl.get_data(self.shape.name, "F23:H26")
        return TeamMemberData.from_raw_excel_data(data)

    def read_building(self) -> TeamMemberData:
        """Return a TeamMemberData object with the Building address from PHPP."""
        data = self.xl.get_data(self.shape.name, "K5:M8")
        return TeamMemberData.from_raw_excel_data(data)

    def read_site_owner(self) -> TeamMemberData:
        """Return a TeamMemberData object with the owner info from PHPP."""
        data = self.xl.get_data(self.shape.name, "K13:M16")
        return TeamMemberData.from_raw_excel_data(data)

    def read_mech_engineer(self) -> TeamMemberData:
        data = self.xl.get_data(self.shape.name, "K18:M21")
        """Return a TeamMemberData object with the ME info from PHPP."""
        return TeamMemberData.from_raw_excel_data(data)

    def read_ph_certification(self) -> TeamMemberData:
        """Return a TeamMemberData object with the Certifier info from PHPP."""
        data = self.xl.get_data(self.shape.name, "K23:M26")
        return TeamMemberData.from_raw_excel_data(data)
