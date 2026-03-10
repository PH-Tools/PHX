# -*- Python Version: 3.10 -*-

"""Core data structures for PPP file format sections."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PppSection:
    """A single PPP section block with header and values."""

    name: str
    rows: int
    cols: int
    values: list[str] = field(default_factory=list)

    def to_lines(self) -> list[str]:
        """Return the section as a list of lines (header + values)."""
        header = f'"{self.name}",{self.rows},{self.cols}'
        return [header] + list(self.values)


@dataclass
class PppFile:
    """An ordered collection of PppSections that serializes to a complete PPP file."""

    sections: list[PppSection] = field(default_factory=list)
    end_marker_after: set[str] = field(
        default_factory=lambda: {
            "Flaechen_Flaecheneingabe_Bauteil_Bezeichnung",
            "Flaechen_Waermebrueckeneingabe_Bezeichnung",
            "Fenster_Bezeichnung_Pos",
        }
    )

    def to_lines(self) -> list[str]:
        """Return all lines for the complete PPP file."""
        lines: list[str] = []
        for section in self.sections:
            lines.extend(section.to_lines())
            if section.name in self.end_marker_after:
                lines.append("<End of designPH import!>")
        return lines
