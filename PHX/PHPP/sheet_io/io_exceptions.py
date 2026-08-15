# -*- Python Version: 3.10 -*-

"""Exceptions used by the IO classes."""


class FindSectionMarkerException(Exception):
    """Raised when a section marker string cannot be found in a worksheet column."""

    def __init__(self, search_string, _sheet_name, _col_letter):
        """Raises when the IO controller cannot find the reference marker in a column."""
        self.msg = (
            f"\n\tError: Cannot find the the marker: '{search_string}' "
            f"in the worksheet '{_sheet_name}' column '{_col_letter}'?"
        )
        super().__init__(self.msg)


class PerReferenceAreaException(Exception):
    """Raised when the PER reference area (TFA or footprint) cannot be found."""

    def __init__(self, _sheet_name, _search_address):
        """Raises when the PER reference area (TFA / Footprint) is missing."""
        self.msg = (
            f"\n\tError: Cannot find the the reference area on '{_sheet_name}' "
            f"worksheet at location '{_search_address}'?"
        )
        super().__init__(self.msg)


class ReadDataException(Exception):
    """Raised when a value cannot be read from a PHPP worksheet cell."""

    def __init__(self, _sheet_name, _read_address):
        """Raised when there is an error reading a value from Excel."""
        self.msg = f"\n\tError: Cannot read the value from '{_sheet_name}' " f"worksheet at location '{_read_address}'?"
        super().__init__(self.msg)


class ResolveComponentIDException(Exception):
    """Raised when a component's PHPP ID cannot be built because its ID cell is empty."""

    def __init__(self, _component_name, _sheet_name, _id_address):
        """Raised when the ID cell beside a matched component name holds no value."""
        self.msg = (
            f"\n\tError: Cannot build the PHPP ID for the component "
            f"'{_component_name}': the ID cell '{_sheet_name}'!{_id_address} is "
            "empty. An unresolvable component ID is never a valid export - PHPP "
            "would silently fail to look the component up. Please check that the "
            "component is entered in the worksheet's entry section."
        )
        super().__init__(self.msg)


class PHPPDataMissingException(Exception):
    """Raised when a required PHPP field returns None."""

    def __init__(self, _sheet_name, _read_address):
        """Raised when there a required field returns 'None'."""
        self.msg = (
            f"Error: Required value missing in PHPP "
            f"worksheet '{_sheet_name}' at cell '{_read_address}'. "
            "Please correct the PHPP."
        )
        super().__init__(self.msg)
