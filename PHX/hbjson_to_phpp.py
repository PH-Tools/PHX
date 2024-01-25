# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Export an HBJSON file to a PHPP excel document."""

import asyncio
import pathlib
import sys

import xlwings as xw

from PHX.from_HBJSON import create_project, read_HBJSON_file
from PHX.PHPP import phpp_app
from PHX.xl import xl_app


async def run(phx_project):
    with phpp_conn.xl.in_silent_mode():
        await phpp_conn.xl.unprotect_all_sheets()
        await phpp_conn.write_certification_config(phx_project)
        await phpp_conn.write_climate_data(phx_project)
        await phpp_conn.write_project_constructions(phx_project)
        await phpp_conn.write_project_tfa(phx_project)
        await phpp_conn.write_project_opaque_surfaces(phx_project)
        await phpp_conn.write_project_thermal_bridges(phx_project)
        await phpp_conn.write_project_window_components(phx_project)
        await phpp_conn.write_project_window_surfaces(phx_project)
        await phpp_conn.write_project_window_shading(phx_project)
        await phpp_conn.write_project_ventilation_components(phx_project)
        await phpp_conn.write_project_ventilators(phx_project)
        await phpp_conn.write_project_spaces(phx_project)
        await phpp_conn.write_project_ventilation_type(phx_project)
        await phpp_conn.write_project_airtightness(phx_project)
        await phpp_conn.write_project_volume(phx_project)
        await phpp_conn.write_project_hot_water(phx_project)
        await phpp_conn.write_project_res_elec_appliances(phx_project)

        if ACTIVATE_VARIANTS == "True":
            await phpp_conn.activate_variant_assemblies()
            await phpp_conn.activate_variant_windows()
            await phpp_conn.activate_variant_ventilation()
            await phpp_conn.activate_variant_additional_vent()


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
    phx_project = create_project.convert_hb_model_to_PhxProject(
        hb_model, _group_components=True
    )

    # --- Connect to open instance of XL, Load the correct PHPP Shape file
    # -------------------------------------------------------------------------
    xl = xl_app.XLConnection(xl_framework=xw, output=print)
    phpp_conn = phpp_app.PHPPConnection(xl)

    try:
        xl.output(f"> connected to excel doc: {phpp_conn.xl.wb.name}")
    except xl_app.NoActiveExcelRunningError as e:
        raise e

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(phx_project))
