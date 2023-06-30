# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""DEV SANDBOX: convert a WUFI XML file over to HBJSON."""

import pathlib

from rich import print
from PHX.from_WUFI_XML.read_WUFI_XML_file import get_WUFI_XML_file_as_dict
from PHX.from_WUFI_XML.phx_converter import convert_WUFI_XML_to_PHX_project
from PHX.to_WUFI_XML import xml_builder, xml_txt_to_file

SOURCE_DIR = pathlib.Path("tests", "_reference_xml")
SOURCE_FILE_NAMES = ["Multi_Room_Complete.xml"]
SOURCE_FILES = [SOURCE_DIR / file for file in SOURCE_FILE_NAMES]
TARGET_DIR = pathlib.Path("tests", "_regenerated_xml")

print(" -" * 50)
for xm_source_file in SOURCE_FILES:
    wufi_xml_data = get_WUFI_XML_file_as_dict(xm_source_file)
    phx_project = convert_WUFI_XML_to_PHX_project(wufi_xml_data)
    print(type(phx_project))

    # --- Output the HBJSON file to WUFI-XML
    target_file = TARGET_DIR / "example.xml"
    xml_txt = xml_builder.generate_WUFI_XML_from_object(phx_project)

    print(f"[bold]> Saving the XML file to: ./{target_file}[/bold]")
    xml_txt_to_file.write_XML_text_file(target_file, xml_txt, False)
