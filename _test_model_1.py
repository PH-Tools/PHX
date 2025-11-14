# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Test the HBJSON>WUFI conversion with Model 1.hbjson which has None energy properties."""

import pathlib

from rich import print

from PHX.from_HBJSON import create_project, read_HBJSON_file
from PHX.to_WUFI_XML import xml_builder, xml_txt_to_file
from tests.conftest import _reload_phx_classes, _reset_phx_class_counters

# -- Test file with None energy properties
SOURCE_FILE = pathlib.Path("sample/hbjson/Model 1.hbjson")
TARGET_FILE = pathlib.Path("sample/Model_1_output.xml")

import logging

logger = logging.getLogger()


def test_model_1_conversion():
    # -- Re-set all the PHX modules (counters)
    _reload_phx_classes()
    _reset_phx_class_counters()

    # --- Read in an existing HB_JSON and re-build the HB Objects
    # -------------------------------------------------------------------------
    print("[bold green]- [/bold green]" * 50)
    print(f"[bold green]> Reading in the HBJSON file: ./{SOURCE_FILE}[/bold green]")
    hb_json_dict = read_HBJSON_file.read_hb_json_from_file(SOURCE_FILE)
    hb_model = read_HBJSON_file.convert_hbjson_dict_to_hb_model(hb_json_dict)

    # --- Generate the PhxProject file.
    # -------------------------------------------------------------------------
    print(f"[bold]> Converting HB Model to PHX Project...[/bold]")
    phx_project = create_project.convert_hb_model_to_PhxProject(
        hb_model, _group_components=True, _merge_faces=True
    )

    # --- Output the WUFI Project as an XML Text File
    # -------------------------------------------------------------------------
    print(f"[bold]> Generating XML Text for the Honeybee Model: [{hb_model}][/bold]")
    xml_txt = xml_builder.generate_WUFI_XML_from_object(phx_project)

    print(f"[bold]> Saving the XML file to: ./{TARGET_FILE}[/bold]")
    xml_txt_to_file.write_XML_text_file(TARGET_FILE, xml_txt, False)
    
    print(f"[bold green]✓ Conversion successful![/bold green]")


if __name__ == "__main__":
    try:
        test_model_1_conversion()
    except Exception as e:
        print(f"[bold red]✗ Conversion failed with error:[/bold red]")
        print(f"[red]{e}[/red]")
        import traceback
        traceback.print_exc()
