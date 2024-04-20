# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Export an HBJSON file to a PHPP excel document."""

import pathlib
import sys

import xlwings as xw

from PHX.from_HBJSON import create_project, read_HBJSON_file
from PHX.PHPP import phpp_app
from PHX.PHPP.phpp_localization.shape_model import PhppShape
from PHX.xl import xl_app

if __name__ == "__main__":
    # --- Command line arguments
    # -------------------------------------------------------------------------
    SOURCE_FILE = pathlib.Path(str(sys.argv[1])).resolve()
    ACTIVATE_VARIANTS = pathlib.Path(sys.argv[2]).resolve()

    # --- Read in an existing HB_JSON and re-build the HB Objects
    # -------------------------------------------------------------------------
    print("- " * 50)
    print(f"> Reading in the HBJSON file: ./{SOURCE_FILE}")
    hb_json_dict = read_HBJSON_file.read_hb_json_from_file(SOURCE_FILE)
    hb_model = read_HBJSON_file.convert_hbjson_dict_to_hb_model(hb_json_dict)

    # --- Generate the PhxProject file.
    # -------------------------------------------------------------------------
    phx_project = create_project.convert_hb_model_to_PhxProject(hb_model, _group_components=True)

    # --- Connect to open instance of XL, Load the correct PHPP Shape file
    # -------------------------------------------------------------------------
    xl = xl_app.XLConnection(xl_framework=xw, output=print)
    phpp_conn = phpp_app.PHPPConnection(xl)

    try:
        xl.output(f"> connected to excel doc: {phpp_conn.xl.wb.name}")
    except xl_app.NoActiveExcelRunningError as e:
        raise e

    with phpp_conn.xl.in_silent_mode():
        phpp_conn.xl.unprotect_all_sheets()
        phpp_conn.write_certification_config(phx_project)
        phpp_conn.write_climate_data(phx_project)
        phpp_conn.write_project_constructions(phx_project)
        phpp_conn.write_project_tfa(phx_project)
        phpp_conn.write_project_opaque_surfaces(phx_project)
        phpp_conn.write_project_thermal_bridges(phx_project)
        phpp_conn.write_project_window_components(phx_project)
        phpp_conn.write_project_window_surfaces(phx_project)
        phpp_conn.write_project_window_shading(phx_project)
        phpp_conn.write_project_ventilation_components(phx_project)
        phpp_conn.write_project_ventilators(phx_project)
        phpp_conn.write_project_spaces(phx_project)
        phpp_conn.write_project_ventilation_type(phx_project)
        phpp_conn.write_project_airtightness(phx_project)
        phpp_conn.write_project_volume(phx_project)
        phpp_conn.write_project_hot_water(phx_project)
        phpp_conn.write_project_res_elec_appliances(phx_project)

        if ACTIVATE_VARIANTS == "True":
            phpp_conn.activate_variant_assemblies()
            phpp_conn.activate_variant_windows()
            phpp_conn.activate_variant_ventilation()
            phpp_conn.activate_variant_additional_vent()
