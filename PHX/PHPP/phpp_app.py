# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Controller for managing the PHPP Connection."""

from typing import Dict, List

from PHX.model import building, certification, components, project
from PHX.model.hvac.collection import NoDeviceFoundError
from PHX.PHPP import phpp_localization, sheet_io
from PHX.PHPP.phpp_localization.shape_model import PhppShape
from PHX.PHPP.phpp_model import (
    areas_data,
    areas_surface,
    areas_thermal_bridges,
    climate_entry,
    component_frame,
    component_glazing,
    component_vent,
    electricity_item,
    hot_water_piping,
    hot_water_tank,
    shading_rows,
    uvalues_constructor,
    vent_ducts,
    vent_space,
    vent_units,
    ventilation_data,
    verification_data,
    version,
    windows_rows,
)
from PHX.xl import xl_app
from PHX.xl.xl_typing import xl_Sheet_Protocol


class PHPPConnection:
    """Interface for a PHPP Excel Document."""

    def __init__(self, _xl: xl_app.XLConnection):
        # -- Setup the Excel connection and facade object.
        self.xl = _xl

        # -- Get the localized (units, language) PHPP Shape with worksheet names and column locations
        self.version = self.get_phpp_version()
        self.shape: PhppShape = phpp_localization.get_phpp_shape(self.xl, self.version)
        self.easyPh = self.is_easyPh()

        # -- Setup all the individual worksheet Classes.
        self.verification = sheet_io.Verification(self.xl, self.shape.VERIFICATION)
        self.climate = sheet_io.Climate(self.xl, self.shape.CLIMATE)
        self.u_values = sheet_io.UValues(self.xl, self.shape.UVALUES)
        self.components = sheet_io.Components(self.xl, self.shape.COMPONENTS)
        self.areas = sheet_io.Areas(self.xl, self.shape.AREAS)
        self.windows = sheet_io.Windows(self.xl, self.shape.WINDOWS)
        self.shading = sheet_io.Shading(self.xl, self.shape.SHADING)
        self.addnl_vent = sheet_io.AddnlVent(self.xl, self.shape.ADDNL_VENT)
        self.heating = sheet_io.HeatingDemand(self.xl, self.shape.HEATING_DEMAND)
        self.heating_load = sheet_io.HeatingPeakLoad(self.xl, self.shape.HEATING_PEAK_LOAD)
        self.cooling = sheet_io.CoolingDemand(self.xl, self.shape.COOLING_DEMAND)
        self.cooling_load = sheet_io.CoolingPeakLoad(self.xl, self.shape.COOLING_PEAK_LOAD)
        self.ventilation = sheet_io.Ventilation(self.xl, self.shape.VENTILATION)
        self.hot_water = sheet_io.HotWater(self.xl, self.shape.DHW)
        self.electricity = sheet_io.Electricity(self.xl, self.shape.ELECTRICITY)
        self.variants = sheet_io.Variants(self.xl, self.shape.VARIANTS)
        self.per = sheet_io.PER(self.xl, self.shape.PER)
        self.overview = sheet_io.Overview(self.xl, self.shape.OVERVIEW)
        self.use_non_res = sheet_io.UseNonRes(self.xl, self.shape.USE_NON_RES)
        self.elec_non_res = sheet_io.ElecNonRes(self.xl, self.shape.ELEC_NON_RES)
        self.ihg_non_res = sheet_io.IhgNonRes(self.xl, self.shape.IHG_NON_RES)
        self.cooling_units = sheet_io.CoolingUnits(self.xl, self.shape.COOLING_UNITS)
        self.solar_dhw = sheet_io.SolarDHW(self.xl, self.shape.SOLAR_DHW)
        self.solar_pv = sheet_io.SolarPV(self.xl, self.shape.SOLAR_PV)

    def get_data_worksheet(self) -> xl_Sheet_Protocol:
        """Return the 'Data' worksheet from the active PHPP file, support English, German, Spanish."""
        valid_data_worksheet_names = ["DATA", "DATEN", "DATOS"]
        worksheet_names = self.xl.get_upper_case_worksheet_names()
        for worksheet_name in valid_data_worksheet_names:
            if worksheet_name in worksheet_names:
                return self.xl.get_sheet_by_name(worksheet_name)

        raise Exception(
            f"Error: Cannot find a '{valid_data_worksheet_names}' worksheet in the Excel file: {self.xl.wb.name}?"
        )

    def get_phpp_version(
        self,
        _search_col: str = "A",
        _row_start: int = 1,
        _row_end: int = 10,
    ) -> version.PHPPVersion:
        """Find the PHPP Version and Language of the active xl-file.

        Arguments:
        ----------
            * _xl (xl_app.XLConnection):
            * _search_col (str)
            * _row_start (int) default=1
            * _row_end (int) default=10

        Returns:
        --------
            * PHPPVersion: The PHPPVersion with a number and Language for the Active PHPP.
        """

        # ---------------------------------------------------------------------
        # -- Find the right 'Data' worksheet
        data_worksheet: xl_Sheet_Protocol = self.get_data_worksheet()

        # ---------------------------------------------------------------------
        # -- Pull the search Column data from the Active XL Instance
        data = self.xl.get_single_column_data(
            _sheet_name=data_worksheet.name,
            _col=_search_col,
            _row_start=_row_start,
            _row_end=_row_end,
        )

        for i, xl_rang_data in enumerate(data, start=_row_start):
            if str(xl_rang_data).upper().strip().replace(" ", "").startswith("PHPP"):
                data_row = i
                break
        else:
            raise Exception(
                f"Error: Cannot determine the PHPP Version? Expected 'PHPP' in"
                f"col: {_search_col} of the {data_worksheet.name} worksheet?"
            )

        # ---------------------------------------------------------------------
        # -- Pull the search row data from the Active XL Instance
        data = self.xl.get_single_row_data(data_worksheet.name, data_row)
        data = [_ for _ in data if _ is not None and _ != ""]  # Filter out all the blanks

        # ---------------------------------------------------------------------
        # -- Find the right Version number
        raw_version_id: str = str(data[1])  # Use the second value in the row - data (will this always work?)
        ver_major, ver_minor = raw_version_id.split(".")

        # ---------------------------------------------------------------------
        # - Figure out the PHPP language
        # - In <v10 the actual language is not noted in the 'Data' worksheet, so
        # - use the PE factor name as a proxy
        language_search_data = {
            "1-PE-FAKTOREN": "DE",
            "1-FACTORES EP": "ES",
            "1-PE-FACTORS": "EN",
        }
        language = None
        for search_string in language_search_data.keys():
            if search_string in str(data[-1]).upper().strip():
                language = language_search_data[search_string]
                language = language.strip().replace(" ", "_").replace(".", "_")
                break
        if not language:
            raise Exception(
                "Error: Cannot determine the PHPP language? Only English, German and Spanish are supported."
            )

        # ---------------------------------------------------------------------
        # -- Build the new PHPPVersion object
        return version.PHPPVersion(ver_major, ver_minor, language)

    def is_easyPh(self) -> bool:
        """Return True if the active PHPP file is an 'easyPH' file."""
        name = self.shape.EASY_PH.name.upper()
        if name in self.xl.get_upper_case_worksheet_names():
            print("PHPP is easyPH")
            return True
        else:
            return False

    def phpp_version_equals_phx_phi_cert_version(self, _phx_variant: project.PhxVariant) -> bool:
        """Return True if the PHX PHI Certification Version and the PHPP Version match."""
        if not int(_phx_variant.phi_certification_major_version) == int(self.version.number_major):
            return False
        return True

    def write_certification_config(self, phx_project: project.PhxProject) -> None:
        if self.easyPh:
            return None

        for phx_variant in phx_project.variants:
            # TODO: how to handle multiple variants?

            if not self.phpp_version_equals_phx_phi_cert_version(phx_variant):
                # -- If the versions don't match, don't try and write anything.
                msg = (
                    f"\nPHPPVersionWarning: the HBJSON PHI "
                    f"Certification version (V={phx_variant.phi_certification_major_version}) "
                    f"does not match the PHPP Version (V={self.version.number_major})? "
                    f"Ignoring all writes to the '{self.shape.VERIFICATION.name}' worksheet.\n"
                )
                self.xl.output(msg)
                return

            # --- Building Type / Use
            self.verification.write_item(
                verification_data.VerificationInput.enum(
                    shape=self.shape.VERIFICATION,
                    input_type="phi_building_category_type",
                    input_enum_value=phx_variant.phi_cert.phi_certification_settings.phi_building_category_type,
                )
            )
            self.verification.write_item(
                verification_data.VerificationInput.enum(
                    shape=self.shape.VERIFICATION,
                    input_type="phi_building_use_type",
                    input_enum_value=phx_variant.phi_cert.phi_certification_settings.phi_building_use_type,
                )
            )
            self.verification.write_item(
                verification_data.VerificationInput.enum(
                    shape=self.shape.VERIFICATION,
                    input_type="phi_building_ihg_type",
                    input_enum_value=phx_variant.phi_cert.phi_certification_settings.phi_building_ihg_type,
                )
            )
            self.verification.write_item(
                verification_data.VerificationInput.enum(
                    shape=self.shape.VERIFICATION,
                    input_type="phi_building_occupancy_type",
                    input_enum_value=phx_variant.phi_cert.phi_certification_settings.phi_building_occupancy_type,
                )
            )

            # --- Certification Config
            self.verification.write_item(
                verification_data.VerificationInput.enum(
                    shape=self.shape.VERIFICATION,
                    input_type="phi_certification_type",
                    input_enum_value=phx_variant.phi_cert.phi_certification_settings.phi_certification_type,
                )
            )
            self.verification.write_item(
                verification_data.VerificationInput.enum(
                    shape=self.shape.VERIFICATION,
                    input_type="phi_certification_class",
                    input_enum_value=phx_variant.phi_cert.phi_certification_settings.phi_certification_class,
                )
            )
            self.verification.write_item(
                verification_data.VerificationInput.enum(
                    shape=self.shape.VERIFICATION,
                    input_type="phi_pe_type",
                    input_enum_value=phx_variant.phi_cert.phi_certification_settings.phi_pe_type,
                )
            )
            self.verification.write_item(
                verification_data.VerificationInput.enum(
                    shape=self.shape.VERIFICATION,
                    input_type="phi_enerphit_type",
                    input_enum_value=phx_variant.phi_cert.phi_certification_settings.phi_enerphit_type,
                )
            )
            self.verification.write_item(
                verification_data.VerificationInput.enum(
                    shape=self.shape.VERIFICATION,
                    input_type="phi_retrofit_type",
                    input_enum_value=phx_variant.phi_cert.phi_certification_settings.phi_retrofit_type,
                )
            )

            # ---- Model Parameters
            if not phx_variant.phius_cert.ph_building_data:
                continue
            self.verification.write_item(
                verification_data.VerificationInput.item(
                    shape=self.shape.VERIFICATION,
                    input_type="num_of_units",
                    input_data=phx_variant.phius_cert.ph_building_data.num_of_units,
                )
            )
            self.verification.write_item(
                verification_data.VerificationInput.item(
                    shape=self.shape.VERIFICATION,
                    input_type="setpoint_winter",
                    input_data=phx_variant.phius_cert.ph_building_data.setpoints.winter,
                    input_unit="C",
                    target_unit=self.shape.VERIFICATION.setpoint_winter.unit,
                )
            )
            self.verification.write_item(
                verification_data.VerificationInput.item(
                    shape=self.shape.VERIFICATION,
                    input_type="setpoint_summer",
                    input_data=phx_variant.phius_cert.ph_building_data.setpoints.summer,
                    input_unit="C",
                    target_unit=self.shape.VERIFICATION.setpoint_summer.unit,
                )
            )

        return None

    def write_climate_data(self, phx_project: project.PhxProject) -> None:
        """Write the variant's weather-station data to the PHPP 'Climate' worksheet."""
        if self.easyPh:
            return None

        for phx_variant in phx_project.variants:
            # -- Write the actual weather station data
            weather_station_data = climate_entry.ClimateDataBlock(shape=self.shape.CLIMATE, phx_site=phx_variant.site)
            self.climate.write_climate_block(weather_station_data)

            # -- Set the active weather station
            active_climate_data = climate_entry.ClimateSettings(shape=self.shape.CLIMATE, phx_site=phx_variant.site)
            self.climate.write_active_climate(active_climate_data)
        return None

    def write_project_constructions(self, phx_project: project.PhxProject) -> None:
        """Write all of the opaque constructions to the PHPP 'U-Values' worksheet."""

        construction_blocks: List[uvalues_constructor.ConstructorBlock] = []
        for phx_construction in phx_project.assembly_types.values():
            construction_blocks.append(
                uvalues_constructor.ConstructorBlock(shape=self.shape.UVALUES, phx_construction=phx_construction)
            )

        self.u_values.write_constructor_blocks(construction_blocks)
        return None

    def write_project_window_components(self, phx_project: project.PhxProject) -> None:
        """Write all of the frame and glass constructions from a PhxProject to the PHPP 'Components' worksheet."""

        glazing_component_rows: List[component_glazing.GlazingRow] = []
        frame_component_rows: List[component_frame.FrameRow] = []
        for phx_construction in phx_project.window_types.values():
            glazing_component_rows.append(
                component_glazing.GlazingRow(shape=self.shape.COMPONENTS, phx_construction=phx_construction)
            )
            frame_component_rows.append(
                component_frame.FrameRow(shape=self.shape.COMPONENTS, phx_construction=phx_construction)
            )
        self.components.write_glazings(glazing_component_rows)
        self.components.write_frames(frame_component_rows)
        return None

    def write_project_ventilation_components(self, phx_project: project.PhxProject) -> None:
        """Write all of the ventilators from a PhxProject to the PHPP 'Components' worksheet."""

        phpp_ventilator_rows: List[component_vent.VentilatorRow] = []
        for phx_variant in phx_project.variants:
            for mech_collection in phx_variant.mech_collections:
                for phx_ventilator in mech_collection.ventilation_devices:
                    new_vent_row = component_vent.VentilatorRow(
                        shape=self.shape.COMPONENTS,
                        phx_vent_sys=phx_ventilator,
                    )
                    phpp_ventilator_rows.append(new_vent_row)
        self.components.write_ventilators(phpp_ventilator_rows)
        return None

    def write_project_tfa(self, phx_project: project.PhxProject) -> None:
        for phx_variant in phx_project.variants:
            self.areas.write_item(
                areas_data.AreasInput(
                    shape=self.shape.AREAS,
                    input_type="tfa_input",
                    input_data=phx_variant.building.tfa_override or phx_variant.building.weighted_net_floor_area,
                    input_unit="M2",
                    target_unit=self.shape.AREAS.tfa_input.unit,
                )
            )
        return None

    def write_project_opaque_surfaces(self, phx_project: project.PhxProject) -> None:
        """Write all of the opaque surfaces from a PhxProject to the PHPP 'Areas' worksheet."""

        surfaces: List[areas_surface.SurfaceRow] = []
        for phx_variant in phx_project.variants:
            for opaque_component in phx_variant.building.opaque_components:
                for phx_polygon in opaque_component.polygons:
                    surfaces.append(
                        areas_surface.SurfaceRow(
                            self.shape.AREAS,
                            phx_polygon,
                            opaque_component,
                            self.u_values.get_constructor_phpp_id_by_name(
                                opaque_component.assembly.display_name, _use_cache=True
                            ),
                            self.version,
                        )
                    )

        if len(surfaces) >= 100:
            print(
                f"Warning: {len(surfaces)} surfaces found in the model. Ensure that you have "
                "added enough rows to the 'Areas' worksheet to handle that many surfaces. "
                "By default the PHPP can only have 100 surfaces input."
            )

        phpp_surfaces_rows_sorted = sorted(surfaces, key=lambda x: x.phx_polygon.display_name.lower())
        self.areas.write_surfaces(phpp_surfaces_rows_sorted)
        return None

    def write_project_thermal_bridges(self, phx_project: project.PhxProject) -> None:
        """Write all of the thermal-bridge elements of a PhxProject to the PHPP 'Areas' worksheet."""

        thermal_bridges: List[areas_thermal_bridges.ThermalBridgeRow] = []
        for variant in phx_project.variants:
            for zone in variant.zones:
                for phx_tb in zone.thermal_bridges:
                    thermal_bridges.append(areas_thermal_bridges.ThermalBridgeRow(self.shape.AREAS, phx_tb))

        if len(thermal_bridges) >= 100:
            print(
                f"Warning: {len(thermal_bridges)} thermal bridges found in the model. Ensure that you have "
                "added enough rows to the 'Areas' worksheet to handle that many thermal bridges. "
                "By default the PHPP can only have 100 thermal bridges input."
            )

        self.areas.write_thermal_bridges(thermal_bridges)
        return None

    def write_project_window_surfaces(self, phx_project: project.PhxProject) -> None:
        """Write all of the window surfaces from a PhxProject to the PHPP 'Windows' worksheet."""

        # -- First, populate the Variant types
        variant_type_names = [
            phx_aperture.variant_type_name
            for phx_variant in phx_project.variants
            for phx_component in phx_variant.building.opaque_components
            for phx_aperture in phx_component.apertures
        ]
        for i, variant_type_name in enumerate(sorted(variant_type_names)):
            self.variants.write_window_type(variant_type_name, i)

        # -- Get the variant types in a dict
        window_type_phpp_ids = self.variants.get_window_type_phpp_ids()

        # -- Write in the window-data
        phpp_windows: List[windows_rows.WindowRow] = []
        for phx_variant in phx_project.variants:
            for phx_component in phx_variant.building.opaque_components:
                for phx_aperture in phx_component.apertures:
                    for ap_polygon in phx_aperture.polygons:
                        host_polygon = phx_component.get_host_polygon_by_child_id_num(ap_polygon.id_num)
                        phpp_host_surface_id_name = self.areas.surfaces.get_surface_phpp_id_by_name(
                            host_polygon.display_name, _use_cache=True
                        )
                        phpp_id_frame = self.components.frames.get_frame_phpp_id_by_name(
                            phx_aperture.window_type.frame_type_display_name,
                            _use_cache=True,
                        )
                        phpp_id_glazing = self.components.glazings.get_glazing_phpp_id_by_name(
                            phx_aperture.window_type.glazing_type_display_name,
                            _use_cache=True,
                        )

                        # TODO: Convert PhxPolygon to PhxPolygonRectangular
                        phpp_windows.append(
                            windows_rows.WindowRow(
                                shape=self.shape.WINDOWS,
                                phx_polygon=ap_polygon,
                                phx_construction=phx_aperture.window_type,
                                phpp_host_surface_id_name=phpp_host_surface_id_name,
                                phpp_id_frame=phpp_id_frame,
                                phpp_id_glazing=phpp_id_glazing,
                                phpp_id_variant_type=window_type_phpp_ids[phx_aperture.variant_type_name].phpp_id,
                            )
                        )

        if len(phpp_windows) >= 150:
            print(
                f"Warning: {len(phpp_windows)} windows found in the model. Ensure that you have "
                "added enough rows to the 'Windows' worksheet to handle that many windows. "
                "By default the PHPP can only have 150 windows input."
            )

        phpp_windows_rows_sorted = sorted(phpp_windows, key=lambda x: x.phx_polygon.display_name.lower())
        self.windows.write_windows(phpp_windows_rows_sorted)
        return None

    def write_project_window_shading(self, phx_project: project.PhxProject) -> None:
        def _get_ap_element_from_dict(
            _window_name: str, _dict: Dict[str, components.PhxApertureElement]
        ) -> components.PhxApertureElement:
            """When reading from excel, it MIGHT come in as a float. This means
            that any windows with a numerical name (ie: '106', '205', etc) will get
            converted to a float in excel (ie: '106' -> 106.0) and get read back in
            that way. To support names 106, 106.0, '106' and '106.0' properly, try them
            with a fallback sequence.
            """

            try:
                # If its a normal string name...
                return _dict[_window_name]
            except KeyError:
                try:
                    # If it is a 'float' name (ie: 106.1)
                    return _dict[str(float(_window_name))]
                except KeyError:
                    try:
                        # If it is an 'int' name (ie: 106)
                        return _dict[str(int(float(_window_name)))]
                    except KeyError as e:
                        raise e

        # Get all the Window worksheet names in order
        window_names = self.windows.get_all_window_names()

        # Get all the PHX Aperture objects
        phx_aperture_dict: Dict[str, components.PhxApertureElement] = {}
        for phx_variant in phx_project.variants:
            for phx_component in phx_variant.building.opaque_components:
                for phx_aperture in phx_component.apertures:
                    for phx_ap_element in phx_aperture.elements:
                        phx_aperture_dict[phx_ap_element.display_name] = phx_ap_element

        # Sort the phx apertures to match the window_names order
        phx_aperture_elements_in_order = (
            _get_ap_element_from_dict(window_name, phx_aperture_dict) for window_name in window_names
        )

        # Write out all the data to the Shading Worksheet
        phpp_shading_rows: List[shading_rows.ShadingRow] = []
        for phx_aperture_element in phx_aperture_elements_in_order:
            phpp_shading_rows.append(
                shading_rows.ShadingRow(
                    self.shape.SHADING,
                    phx_aperture_element.shading_dimensions,
                    phx_aperture_element.winter_shading_factor,
                    phx_aperture_element.summer_shading_factor,
                )
            )

        self.shading.write_shading(phpp_shading_rows)

        # TODO: option to clear all the dimensional info?

        return None

    def write_project_ventilators(self, phx_project: project.PhxProject) -> None:
        """Write all of the used Ventilator Units from a PhxProject to the PHPP 'Additional Vent' worksheet."""
        if self.easyPh:
            return None

        phpp_vent_unit_rows: List[vent_units.VentUnitRow] = []
        for phx_variant in phx_project.variants:
            for mech_collection in phx_variant.mech_collections:
                for phx_ventilator in mech_collection.ventilation_devices:
                    phpp_id_ventilator = self.components.ventilators.get_ventilator_phpp_id_by_name(
                        phx_ventilator.display_name
                    )
                    new_vent_row = vent_units.VentUnitRow(
                        shape=self.shape.ADDNL_VENT,
                        phx_vent_sys=phx_ventilator,
                        phpp_id_ventilator=phpp_id_ventilator,
                    )
                    phpp_vent_unit_rows.append(new_vent_row)

        self.addnl_vent.write_vent_units(phpp_vent_unit_rows)
        return None

    def write_project_spaces(self, phx_project: project.PhxProject) -> None:
        """Write all of the PH-Spaces from a PhxProject to the PHPP 'Additional Vent' worksheet."""
        if self.easyPh:
            return None

        phpp_vent_rooms: List[vent_space.VentSpaceRow] = []
        for phx_variant in phx_project.variants:
            for zone in phx_variant.building.zones:
                for room in zone.spaces:
                    # -- Find the right Ventilator assigned to the Space.
                    try:
                        phx_mech_ventilator = phx_variant.get_mech_device_by_id(room.vent_unit_id_num)
                        phpp_id_ventilator = self.components.ventilators.get_ventilator_phpp_id_by_name(
                            phx_mech_ventilator.display_name
                        )
                        phpp_row_ventilator = self.addnl_vent.vent_units.get_vent_unit_num_by_phpp_id(
                            phpp_id_ventilator
                        )
                    except NoDeviceFoundError:
                        # If no ventilation system / unit has not been applied yet
                        phpp_row_ventilator = None

                    phx_vent_pattern = phx_project.utilization_patterns_ventilation.get_pattern_by_id_num(
                        room.ventilation.schedule.id_num
                    )

                    phpp_rm = vent_space.VentSpaceRow(
                        shape=self.shape.ADDNL_VENT,
                        phx_room_vent=room,
                        phpp_row_ventilator=phpp_row_ventilator,
                        phx_vent_pattern=phx_vent_pattern,
                    )
                    phpp_vent_rooms.append(phpp_rm)

        if len(phpp_vent_rooms) >= 30:
            print(
                f"Warning: {len(phpp_vent_rooms)} spaces found in the model. Ensure that you have "
                "added enough rows to the 'Additional Vent' worksheet to handle that many spaces. "
                "By default the PHPP can only have 30 spaces input."
            )

        self.addnl_vent.write_spaces(phpp_vent_rooms)
        return None

    def write_project_ventilation_type(self, phx_project: project.PhxProject) -> None:
        """Set the Ventilation-Type to the PHPP 'Ventilation' worksheet."""
        if self.easyPh:
            return None

        for variant in phx_project.variants:
            self.ventilation.write_ventilation_type(
                # TODO: Get the actual type from the model someplace?
                # TODO: How to combine Variants?
                ventilation_data.VentilationInputItem.vent_type(
                    self.shape.VENTILATION, "1-Balanced PH ventilation with HR"
                )
            )
            self.ventilation.write_multi_vent_worksheet_on(
                ventilation_data.VentilationInputItem.multi_unit_on(self.shape.VENTILATION, "x")
            )
        return None

    def write_project_volume(self, phx_project: project.PhxProject) -> None:
        """Write the Vn50 and Vv to the PHPP 'Ventilation Worksheet."""
        if self.easyPh:
            return None

        for variant in phx_project.variants:
            # TODO: How to handle multiple variants?

            if not variant.phius_cert.ph_building_data:
                continue
            bldg: building.PhxBuilding = variant.building

            self.ventilation.write_Vn50_volume(
                ventilation_data.VentilationInputItem.airtightness_Vn50(self.shape.VENTILATION, bldg.net_volume)
            )

    def write_project_airtightness(self, phx_project: project.PhxProject) -> None:
        """Write the Airtightness data to the PHPP 'Ventilation' worksheet."""
        if self.easyPh:
            return None

        for variant in phx_project.variants:
            # TODO: How to handle multiple variants?

            if not variant.phius_cert.ph_building_data:
                continue
            ph_bldg: certification.PhxPhBuildingData = variant.phius_cert.ph_building_data

            # TODO: Get the actual values from the Model somehow
            self.ventilation.write_wind_coeff_e(
                ventilation_data.VentilationInputItem.wind_coeff_e(self.shape.VENTILATION, ph_bldg.wind_coefficient_e)
            )
            self.ventilation.write_wind_coeff_f(
                ventilation_data.VentilationInputItem.wind_coeff_f(self.shape.VENTILATION, ph_bldg.wind_coefficient_f)
            )
            self.ventilation.write_airtightness_n50(
                ventilation_data.VentilationInputItem.airtightness_n50(self.shape.VENTILATION, ph_bldg.airtightness_n50)
            )
        return None

    def write_project_hot_water(self, phx_project: project.PhxProject) -> None:
        """Write the Hot Water data to the PHPP 'DHW+Distribution' worksheet."""
        if self.easyPh:
            return None

        for variant in phx_project.variants:
            mech_collection = variant.default_mech_collection

            # -- Tanks
            # Use only the first 2 tanks for PHPP
            if len(mech_collection.dhw_tank_devices) > 2:
                print(
                    f"Warning: PHPP only allows 2 tanks."
                    f"{len(mech_collection.dhw_tank_devices)} tank"
                    f'found in the Variant "{variant.name}"'
                )

            tank_inputs = []
            for i, phx_dhw_tank in enumerate(mech_collection.dhw_tank_devices[:2], start=1):
                tank_inputs.append(
                    hot_water_tank.TankInput(
                        self.shape.DHW,
                        phx_dhw_tank,  # type: water.PhxHotWaterTank
                        i,
                    )
                )
            self.hot_water.write_tanks(tank_inputs)

            # -- Branch Piping
            branch_piping_inputs = []
            branch_pipe_groups = mech_collection.dhw_distribution_piping_segments_by_diam
            if len(branch_pipe_groups) > 5:
                print(
                    "Warning: PHPP only allows 5 groups of DHW branch piping. "
                    f"{len(branch_pipe_groups)} piping groups "
                    f'found in the Variant "{variant.name}". '
                    "Using only then first 5 piping groups."
                )

            for i, phx_branch_piping in enumerate(branch_pipe_groups[:5]):
                branch_piping_inputs.append(
                    hot_water_piping.BranchPipingInput(
                        self.shape.DHW,
                        phx_branch_piping,  # type: piping.PhxPipeSegment
                        i,
                        mech_collection._distribution_num_hw_tap_points,
                    )
                )
            self.hot_water.write_branch_piping(branch_piping_inputs)

            # -- Recirculation Piping
            recirc_piping_inputs = []
            recirc_pipe_groups = mech_collection.dhw_recirc_piping_segments_by_diam
            if len(recirc_pipe_groups) > 5:
                print(
                    "Warning: PHPP only allows 5 groups of DHW Recirc. piping. "
                    f"{len(recirc_pipe_groups)} piping groups "
                    f'found in the Variant "{variant.name}". '
                    "Using only then first 5 piping groups."
                )

            for i, phx_recirc_piping in enumerate(recirc_pipe_groups[:5]):
                recirc_piping_inputs.append(
                    hot_water_piping.RecircPipingInput(
                        self.shape.DHW,
                        phx_recirc_piping,  # type: piping.PhxPipeSegment
                        i,
                    )
                )
            self.hot_water.write_recirc_piping(recirc_piping_inputs)

        return None

    def write_project_res_elec_appliances(self, phx_project: project.PhxProject) -> None:
        """Write out all of the detailed residential appliances to the "Electricity" Worksheet."""
        if self.easyPh:
            return None

        equipment_inputs = []
        for phx_variant in phx_project.variants:
            for zone in phx_variant.building.zones:
                for phx_equip in zone.elec_equipment_collection:
                    equipment_inputs.append(electricity_item.ElectricityItemXLWriter(phx_equip))
            self.electricity.write_equipment(equipment_inputs)

        return None

    def write_non_res_utilization_profiles(self, phx_project: project.PhxProject) -> None:
        """Write out all of the Utilization patterns to the "Use non-res" Worksheet."""
        if self.easyPh:
            return None

        # TODO: build this....
        # for pattern in phx_project.utilization_patterns_occupancy:
        #     print(pattern)

    def write_non_res_space_lighting(self, phx_project: project.PhxProject) -> None:
        """Write out all of the Space Lighting values to the "Electricity non-res" Worksheet."""
        if self.easyPh:
            return None

        return

    def write_non_res_IHG(self, phx_project: project.PhxProject) -> None:
        """Write out all of the Occupancy patterns to the "IHG non-res" Worksheet."""
        if self.easyPh:
            return None

        return

    def activate_variant_assemblies(self) -> None:
        """Remove all existing U-Value information and link assemblies to the Variants worksheet."""
        if self.easyPh:
            return None

        # -- Collect all the assemblies from the U-Values page
        # -- and add each one to the Variants assembly-layers section
        for i, assembly_name in enumerate(self.u_values.get_used_constructor_names(), start=0):
            if i > 25:
                print(
                    "WARNING: The Variants worksheet can only handle 26 different assemblies."
                    "You will have to set up the assembly-layer Variants links manually."
                )
                continue
            self.variants.write_assembly_layer(assembly_name, i)

        # -- Get all the Variant assembly names with prefix
        assembly_phpp_ids = self.variants.get_assembly_layer_phpp_ids()

        # -- Make all Variants--->U-Values links
        self.u_values.activate_variants(assembly_phpp_ids)

        return None

    def activate_variant_windows(self) -> None:
        """Set the Frame and Glass Components to link to the Variants worksheet for all windows."""
        if self.easyPh:
            return None

        self.windows.activate_variants()

        return None

    def activate_variant_ventilation(self) -> None:
        """Set the ACH, Ventilation type to link to the Variants worksheet."""
        if self.easyPh:
            return None

        self.ventilation.activate_variants()

        return None

    def activate_variant_additional_vent(self) -> None:
        """Set the Ventilator, duct length and insulation to link to the Variants worksheet."""
        if self.easyPh:
            return None

        # -- Find the locations of the Ventilation input items
        input_item_rows = self.variants.get_ventilation_input_item_rows()
        vent_unit_row = input_item_rows[self.shape.VARIANTS.ventilation.input_item_names.ventilator_unit]

        self.addnl_vent.activate_variants(
            variants_worksheet_name=self.shape.VARIANTS.name,
            vent_unit_range=f"{self.shape.VARIANTS.active_value_column}{vent_unit_row}",
        )

        return None
