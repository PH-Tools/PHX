# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Controller Class for the PHPP 'Overview' Worksheet."""

from __future__ import annotations

from ph_units.unit_type import Unit

from PHX.PHPP.phpp_localization import shape_model as shp
from PHX.PHPP.sheet_io.io_exceptions import PHPPDataMissingException
from PHX.xl.xl_app import XLConnection


class OverviewBasicData:
    def __init__(self, _host, _xl: XLConnection, _shape: shp.OverviewBasicData):
        self.host = _host
        self.xl = _xl
        self.shape = _shape

    def get_num_dwellings(self) -> int:
        """Return the Total Net Interior Volume (Vn50)

        They put res and non-res dwelling num on different columns?
        """
        address_res = self.shape.address_number_dwellings_res
        val_res = self.xl.get_single_data_item(self.host.worksheet_name, address_res)
        if val_res:
            return int(val_res)

        address_nonres = self.shape.address_number_dwellings_nonres
        val_nonres = self.xl.get_single_data_item(self.host.worksheet_name, address_nonres)
        if val_nonres:
            return int(val_nonres)

        raise PHPPDataMissingException(self.host.worksheet_name, [address_res, address_nonres])

    def get_num_occupants(self) -> float:
        """Return the number of occupants.

        Note: They put res and non-res occupancy on different columns?
        """
        address_res = self.shape.address_number_occupants_res
        val_res = self.xl.get_single_data_item(self.host.worksheet_name, address_res)
        if val_res:
            return float(val_res)

        address_nonres = self.shape.address_number_occupants_nonres
        val_nonres = self.xl.get_single_data_item(self.host.worksheet_name, address_nonres)
        if val_nonres:
            return float(val_nonres)

        raise PHPPDataMissingException(self.host.worksheet_name, [address_res, address_nonres])

    def get_project_name(self) -> str:
        """Return the name of the Project / Building"""
        address = self.shape.address_project_name
        val = self.xl.get_single_data_item(self.host.worksheet_name, address)
        if val:
            return str(val)

        raise PHPPDataMissingException(self.host.worksheet_name, address)


class OverviewVentilation:
    def __init__(self, _host, _xl: XLConnection, _shape: shp.OverviewVentilation) -> None:
        self.host = _host
        self.xl = _xl
        self.shape = _shape

    def get_vn50(self) -> Unit:
        """Return the Total Net Interior Volume (Vn50)"""
        address = self.shape.vn50.xl_range
        val = self.xl.get_single_data_item(self.host.worksheet_name, address)
        return Unit(float(val or 0.0), str(self.shape.vn50.unit))


class OverviewBuildingEnvelope:
    """IO Controller for the PHPP 'Overview' worksheet."""

    def __init__(self, _host, _xl: XLConnection, _shape: shp.OverviewBuildingEnvelope) -> None:
        self.host = _host
        self.xl = _xl
        self.shape = _shape

    def get_area_envelope(self) -> Unit:
        """Return the Total Envelope Area [M2]"""
        address = self.shape.address_area_envelope.xl_range
        val = self.xl.get_single_data_item(self.host.worksheet_name, address)
        return Unit(float(val or 0.0), str(self.shape.address_area_envelope.unit))

    def get_area_tfa(self) -> Unit:
        """Return the Total TFA [M2]"""
        address = self.shape.address_area_tfa.xl_range
        val = self.xl.get_single_data_item(self.host.worksheet_name, address)
        return Unit(float(val or 0.0), str(self.shape.address_area_tfa.unit))


class Overview:
    """IO Controller for the PHPP 'Overview' worksheet."""

    def __init__(self, _xl: XLConnection, _shape: shp.Overview) -> None:
        self.xl = _xl
        self.shape = _shape
        self.basic_data = OverviewBasicData(self, _xl, self.shape.basic_data)
        self.building_envelope = OverviewBuildingEnvelope(self, _xl, self.shape.building_envelope)
        self.ventilation = OverviewVentilation(self, _xl, self.shape.ventilation)

    @property
    def worksheet_name(self) -> str:
        return self.shape.name

    def get_area_envelope(self) -> Unit:
        """Return the Total Envelope Area [M2 | FT2]"""
        return self.building_envelope.get_area_envelope()

    def get_area_tfa(self) -> Unit:
        """Return the Total TFA [M2 | FT2]"""
        return self.building_envelope.get_area_tfa()

    def get_net_interior_volume(self) -> Unit:
        """Return the Total Net Interior Volume (Vn50) [M3 | FT3]"""
        return self.ventilation.get_vn50()

    def get_number_of_dwellings(self) -> int:
        """Return the total number of dwellings."""
        return self.basic_data.get_num_dwellings()

    def get_number_of_occupants(self) -> float:
        """Return the total number of occupants."""
        return self.basic_data.get_num_occupants()

    def get_project_name(self) -> str:
        """Return the Name of the Project."""
        return self.basic_data.get_project_name()
