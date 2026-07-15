# -*- Python Version: 3.10 -*-

"""Export an HBJSON file to a PHPP excel document."""

import pathlib
import sys

from PHX.from_HBJSON import create_project, read_HBJSON_file
from PHX.PHPP import phpp_app


def write_phx_project_to_phpp(
    phpp_conn: "phpp_app.PHPPConnection", phx_project, activate_variants: bool = False
) -> None:
    """Write a complete PhxProject to an open PHPP document.

    This is the canonical PHPP write sequence. It is used by the command-line
    export (below) and by the performance-profiling harness in 'scripts/perf/'
    so that profiled runs always execute the exact production sequence.

    Note: the caller is responsible for wrapping this in 'xl.in_silent_mode()'
    and for un-protecting the sheets first.

    Arguments:
    ----------
        * phpp_conn (phpp_app.PHPPConnection): An open PHPP connection.
        * phx_project (PhxProject): The PhxProject to write to the PHPP.
        * activate_variants (bool): Set True to activate the PHPP 'Variants'
            inputs after writing. Default=False.

    Returns:
    --------
        * None
    """
    phpp_conn.write_certification_config(phx_project)
    phpp_conn.write_climate_data(phx_project)
    # Note: have to re-calc after Climate is set to avoid having any 'errors' in
    # PHPP cells. Errors will cause XLWings to silently skip the cell, resulting in
    # erroneous counts when locating write rows (ie: Ventilation Components)
    phpp_conn.calculate()
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

    if activate_variants:
        phpp_conn.activate_variant_assemblies()
        phpp_conn.activate_variant_windows()
        phpp_conn.activate_variant_ventilation()
        phpp_conn.activate_variant_additional_vent()


if __name__ == "__main__":
    import xlwings as xw

    from PHX.xl import xl_app

    # --- Command line arguments
    # -------------------------------------------------------------------------
    SOURCE_FILE = pathlib.Path(str(sys.argv[1])).resolve()
    ACTIVATE_VARIANTS = pathlib.Path(sys.argv[2]).resolve()

    # --- Read in an existing HB_JSON and re-build the HB Objects
    # -------------------------------------------------------------------------
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
        write_phx_project_to_phpp(phpp_conn, phx_project, activate_variants=(ACTIVATE_VARIANTS == "True"))
