# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""Functions for importing WUFI XML file data."""

from typing import Dict, Any
import pathlib
from lxml import etree


def xml_to_dict(element, _level=0) -> Dict[str, Any]:
    d = {}

    if len(element) == 0:
        # -- If its a bar element with no children, just return the text
        # -- Debug
        tag = f"{_level * '  '} {element.tag :<35}"
        attrib = getattr(element, "attrib", "")
        l = len(element)
        # print(f"{tag} | {attrib} | {l}")

        return element.text

    for child in element:
        # -- Debug
        tag = f"{_level * '  '} {child.tag :<35}"
        attrib = getattr(child, "attrib", "")
        l = len(child)
        # print(f"{tag} | {attrib} | {l}")

        if len(child) == 0:
            # At the end of the a branch
            if "count" in child.attrib:
                # It is just an empty container
                d[child.tag] = []
            else:
                # It is an actual data item
                d[child.tag] = child.text
        elif "count" in getattr(child, "attrib", ""):
            # -- The children of this node should be in a list
            d[child.tag] = []
            for sub_child in child:
                d[child.tag].append(xml_to_dict(sub_child, _level + 1))
        else:
            # -- The children of this node are other nodes
            d[child.tag] = xml_to_dict(child, _level + 1)
    return d


def get_WUFI_XML_file_as_dict(_file_address: pathlib.Path) -> Dict[str, Any]:
    """Read in the WUFI-XML file and return the data as a dictionary."""

    parser = etree.XMLPullParser(recover=True, encoding="utf-8")
    with open(_file_address, mode="r", encoding="utf-8") as xml_file:
        # -- Read in chunks in case the file is large
        while True:
            chunk = xml_file.read(1024)
            if not chunk:
                break
            parser.feed(chunk)

    # Get the root element of the parsed XML
    root = parser.close()

    # Convert the root element and all children to a Python Dictionary
    return xml_to_dict(root)


def get_WUFI_xml_file_as_str(_file_address: pathlib.Path) -> str:
    """Read in the WUFI-XML file and return it as a string.

    Arguments:
    ----------
        _file_address (pathlib.Path): A valid file path for the WUFI-XML file to read.

    Returns:
    --------
        str: The WUFI XML text, read in from the WUFI-XML file.
    """

    with open(_file_address) as xml_file:
        data = xml_file.read()
    return data
