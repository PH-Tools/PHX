# -*- Python Version: 3.10 -*-

"""Tests for PPP section data structures."""

from PHX.to_PPP.ppp_sections import PppFile, PppSection


def test_ppp_section_to_lines_single_col():
    s = PppSection("test_section", 3, 1, ["a", "b", "c"])
    lines = s.to_lines()
    assert lines[0] == '"test_section",3,1'
    assert lines[1:] == ["a", "b", "c"]
    assert len(lines) == 4


def test_ppp_section_to_lines_multi_col():
    s = PppSection("multi", 2, 3, ["r1c1", "r1c2", "r1c3", "r2c1", "r2c2", "r2c3"])
    lines = s.to_lines()
    assert lines[0] == '"multi",2,3'
    assert len(lines) == 7


def test_ppp_file_end_markers():
    sections = [
        PppSection("Flaechen_Flaecheneingabe_Bauteil_Bezeichnung", 3, 1, ["Floor", "-", "-"]),
        PppSection("Flaechen_Waermebrueckeneingabe_Bezeichnung", 2, 1, ["-", "-"]),
        PppSection("Fenster_Bezeichnung_Pos", 2, 1, ["001", "-"]),
        PppSection("other_section", 1, 1, ["x"]),
    ]
    f = PppFile(sections=sections)
    lines = f.to_lines()
    markers = [l for l in lines if "End of designPH" in l]
    assert len(markers) == 3
    # Markers replace the last data value (no extra lines added)
    assert lines == [
        '"Flaechen_Flaecheneingabe_Bauteil_Bezeichnung",3,1',
        "Floor",
        "-",
        "<End of designPH import!>",
        '"Flaechen_Waermebrueckeneingabe_Bezeichnung",2,1',
        "-",
        "<End of designPH import!>",
        '"Fenster_Bezeichnung_Pos",2,1',
        "001",
        "<End of designPH import!>",
        '"other_section",1,1',
        "x",
    ]


def test_ppp_file_no_extra_markers():
    sections = [
        PppSection("some_random_section", 2, 1, ["a", "b"]),
    ]
    f = PppFile(sections=sections)
    lines = f.to_lines()
    markers = [l for l in lines if "End of designPH" in l]
    assert len(markers) == 0
