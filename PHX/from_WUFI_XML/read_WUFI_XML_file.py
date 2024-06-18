# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Functions for importing WUFI XML file data."""

import pathlib
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

from lxml import etree


@dataclass
class Tag:
    text: Optional[str]
    tag: str
    attrib: Optional[Dict[str, str]]


def _is_list_element(_child) -> bool:
    if "count" in getattr(_child, "attrib", ""):
        return True

    # -- WUFI NONSENSE....Why the fuck don't THESE have a 'count'?
    elif _child.tag == "PEFactorsUserDef":
        return True
    elif _child.tag == "CO2FactorsUserDef":
        return True
    return False


def xml_to_dict(element: etree._Element, _level: int = 0) -> Dict[Union[List, str], Any]:
    d = {}

    if len(element) == 0:
        # -- If its a bare element with no children, just return the text
        # -- Debug
        tag = f"{_level * '  '} {element.tag :<35}"
        attrib = getattr(element, "attrib", "")
        l = len(element)

        return {element.tag: Tag(element.text, element.tag, element.attrib)}

    for child in element:  # type: ignore
        # -- Debug
        tag = f"{_level * '  '} {child.tag :<35}"
        attrib = getattr(child, "attrib", "")
        l = len(child)
        # ---

        if len(child) == 0:
            # At the end of the a branch
            if "count" in child.attrib:
                # It is just an empty container
                d[child.tag] = []
            else:
                # It is finally an actual data item
                d[child.tag] = Tag(child.text, child.tag, child.attrib)  # .text
        elif _is_list_element(child):
            # -- Oy... WUFI... sometimes the unit data is up at the parent
            if "unit" in getattr(child, "attrib", ""):
                for _ in child:
                    _.attrib["unit"] = child.attrib.get("unit", "")

            # -- The children of this node should be in a list
            d[child.tag] = []
            for sub_child in child:
                d[child.tag].append(xml_to_dict(sub_child, _level + 1))

        else:
            d[child.tag] = xml_to_dict(child, _level + 1)
    return d


def get_WUFI_XML_file_as_dict(_file_address: pathlib.Path) -> Dict[Union[str, List], Any]:
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
    root: etree._Element = parser.close()

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


def string_to_xml_dict(xml_str: str) -> Dict:
    """Take a string, and convert it to a dict of XML elements."""
    parser = etree.XMLParser(remove_comments=True)
    root = etree.fromstring(xml_str, parser=parser)
    return {child.tag: child.text for child in root}
