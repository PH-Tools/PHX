# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""DEV SANDBOX: convert a WUFI XML file over to HBJSON."""

import pathlib

from rich import print

from PHX.from_WUFI_XML.phx_converter import convert_WUFI_XML_to_PHX_project
from PHX.from_WUFI_XML.read_WUFI_XML_file import get_WUFI_XML_file_as_dict
from PHX.from_WUFI_XML.wufi_file_schema import WUFIplusProject
from PHX.to_WUFI_XML import xml_builder, xml_txt_to_file

SOURCE_DIR = pathlib.Path("tests", "_test_reference_files_xml")
SOURCE_FILE_NAMES = ["School.xml", "_la_mora.xml", "_ridgeway.xml"]
TARGET_DIR = pathlib.Path("tests", "_regenerated_xml")

print(" -" * 50)
for i, xm_source_file_name in enumerate(SOURCE_FILE_NAMES):
    xm_source_file = SOURCE_DIR / xm_source_file_name

    # ----------------------------------------------------------------
    # -- 1) Read in the WUFI-XML File as a new Pydantic Model
    print(f"[green bold]> Reading in data from XML-File: {xm_source_file}[/green bold]")
    wufi_xml_data = get_WUFI_XML_file_as_dict(xm_source_file)
    wufi_xml_model = WUFIplusProject.parse_obj(wufi_xml_data)

    # ----------------------------------------------------------------
    # -- 2) Convert the Pydantic WUFI model over to a PHX model
    print(f"[green bold]> Converting XML-data to a PHX-Model[/green bold]")
    phx_project = convert_WUFI_XML_to_PHX_project(wufi_xml_model)

    # ----------------------------------------------------------------
    # -- 3) Output the PHX model back to a WUFI-XML
    target_file = TARGET_DIR / xm_source_file_name
    xml_txt = xml_builder.generate_WUFI_XML_from_object(phx_project)

    # ----------------------------------------------------------------
    # -- 4) Save the XML file
    print(f"[bold]> Saving the XML file to: ./{target_file}[/bold]")
    xml_txt_to_file.write_XML_text_file(target_file, xml_txt, False)
