# -*- Python Version: 3.10 -*-

"""Write a PppFile to disk as UTF-16LE with BOM."""

from __future__ import annotations

import pathlib

from PHX.to_PPP.ppp_sections import PppFile


def write_ppp_file(_filepath: pathlib.Path, _ppp_file: PppFile) -> None:
    """Write a PppFile to disk as a UTF-16LE encoded text file with BOM."""
    lines = _ppp_file.to_lines()
    text = "\n".join(lines)
    with open(_filepath, "w", encoding="utf-16-le") as f:
        f.write("\ufeff")  # BOM
        f.write(text)
