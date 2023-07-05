# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""DEV SANDBOX: convert a WUFI XML file over to HBJSON."""

import pathlib

from rich import print
from PHX.from_WUFI_XML.read_WUFI_XML_file import get_WUFI_XML_file_as_dict
from PHX.from_WUFI_XML.phx_converter import convert_WUFI_XML_to_PHX_project
from PHX.to_WUFI_XML import xml_builder, xml_txt_to_file

from PHX.from_WUFI_XML.wufi_file_schema import WUFIplusProject

SOURCE_DIR = pathlib.Path("tests", "_reference_xml")
SOURCE_FILE_NAMES = [
    "test_apartment.xml",
]
TARGET_DIR = pathlib.Path("tests", "_regenerated_xml")

print(" -" * 50)
for i, xm_source_file_name in enumerate(SOURCE_FILE_NAMES):
    print(f" -" * 25)
    xm_source_file = SOURCE_DIR / xm_source_file_name

    # ----------------------------------------------------------------
    # -- Read in the WUFI-XML File as a new Pydantic Model
    print(f"[green bold]> Reading in the file: {xm_source_file}[/green bold]")
    wufi_xml_data = get_WUFI_XML_file_as_dict(xm_source_file)
    wufi_xml_model = WUFIplusProject.parse_obj(wufi_xml_data)

    # with open(f"dict_{i}.txt", "w") as f:
    #     print(wufi_xml_data, file=f)

    # with open(f"model_{i}.txt", "w") as f:
    #     print(wufi_xml_model, file=f)

    # ----------------------------------------------------------------
    # Convert the Pydnatic WUFI model over to a PHX model
    print(f"[green bold]> Converting XML file to PHX Model[/green bold]")
    phx_project = convert_WUFI_XML_to_PHX_project(wufi_xml_model)

    # # # # --- Output the PHX model to a WUFI-XML
    target_file = TARGET_DIR / xm_source_file_name
    xml_txt = xml_builder.generate_WUFI_XML_from_object(phx_project)

    print(f"[bold]> Saving the XML file to: ./{target_file}[/bold]")
    xml_txt_to_file.write_XML_text_file(target_file, xml_txt, False)
