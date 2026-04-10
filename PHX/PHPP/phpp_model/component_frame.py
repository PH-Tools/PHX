# -*- Python Version: 3.10 -*-

"""Model class for a PHPP Components/Window-Frame row."""

from collections import defaultdict
from dataclasses import dataclass
from functools import partial

from PHX.model import constructions
from PHX.PHPP.phpp_localization import shape_model
from PHX.xl import xl_data


@dataclass
class FrameRow:
    """A single Areas/Surface entry row."""

    __slots__ = (
        "shape",
        "phx_construction",
    )
    shape: shape_model.Components
    phx_construction: constructions.PhxConstructionWindow

    def _create_range(self, _field_name: str, _row_num: int) -> str:
        """Return the XL Range ("P12",...) for the specific field name."""
        col = getattr(self.shape.frames.inputs, _field_name).column
        return f"{col}{_row_num}"

    def _get_column(self, _field_name: str) -> str:
        """Return the column letter(s) for the specific field name."""
        return getattr(self.shape.frames.inputs, _field_name).column

    def _get_target_unit(self, _field_name: str) -> str:
        "Return the right target unit for the PHPP item writing (IP | SI)"
        return getattr(self.shape.frames.inputs, _field_name).unit

    def _build_averaged_psi_items(
        self,
        _sheet_name: str,
        _row_num: int,
        _field_names: list[str],
        _values: list[float],
        _input_unit: str,
    ) -> list[xl_data.XlItem]:
        """Build XlItems for psi fields, averaging values that share a column.

        When multiple per-side psi values map to the same PHPP column (e.g. PHPP 10.x
        has a single psi-glazing column for all four sides), write one item with the
        average. When columns differ (PHPP 9.x), write individual items.
        """
        groups: defaultdict[str, list[tuple[str, float]]] = defaultdict(list)
        for field_name, value in zip(_field_names, _values):
            col = self._get_column(field_name)
            groups[col].append((field_name, value))

        items: list[xl_data.XlItem] = []
        for col, entries in groups.items():
            avg_value = sum(v for _, v in entries) / len(entries)
            first_field = entries[0][0]
            items.append(
                xl_data.XlItem(
                    _sheet_name,
                    f"{col}{_row_num}",
                    avg_value,
                    _input_unit,
                    self._get_target_unit(first_field),
                )
            )
        return items

    def create_xl_items(self, _sheet_name: str, _row_num: int) -> list[xl_data.XlItem]:
        """Returns a list of the XL Items to write for this Surface Entry

        Arguments:
        ----------
            * _sheet_name: (str) The name of the worksheet to write to.
            * _row_num: (int) The row number to build the XlItems for
        Returns:
        --------
            * (List[XlItem]): The XlItems to write to the sheet.
        """
        create_range = partial(self._create_range, _row_num=_row_num)
        XLItemCompo = partial(xl_data.XlItem, _sheet_name)
        xl_item_list: list[xl_data.XlItem] = [
            XLItemCompo(
                create_range("description"),
                f"'{self.phx_construction.frame_type_display_name}",
            ),
            XLItemCompo(
                create_range("u_value_left"),
                self.phx_construction.frame_left.u_value,
                "W/M2K",
                self._get_target_unit("u_value_left"),
            ),
            XLItemCompo(
                create_range("u_value_right"),
                self.phx_construction.frame_right.u_value,
                "W/M2K",
                self._get_target_unit("u_value_right"),
            ),
            XLItemCompo(
                create_range("u_value_bottom"),
                self.phx_construction.frame_bottom.u_value,
                "W/M2K",
                self._get_target_unit("u_value_bottom"),
            ),
            XLItemCompo(
                create_range("u_value_top"),
                self.phx_construction.frame_top.u_value,
                "W/M2K",
                self._get_target_unit("u_value_top"),
            ),
            XLItemCompo(
                create_range("width_left"),
                self.phx_construction.frame_left.width,
                "M",
                self._get_target_unit("width_left"),
            ),
            XLItemCompo(
                create_range("width_right"),
                self.phx_construction.frame_right.width,
                "M",
                self._get_target_unit("width_right"),
            ),
            XLItemCompo(
                create_range("width_bottom"),
                self.phx_construction.frame_bottom.width,
                "M",
                self._get_target_unit("width_bottom"),
            ),
            XLItemCompo(
                create_range("width_top"),
                self.phx_construction.frame_top.width,
                "M",
                self._get_target_unit("width_top"),
            ),
        ]

        # -- psi-glazing: average values that share a column (PHPP 10.x → single col)
        xl_item_list.extend(
            self._build_averaged_psi_items(
                _sheet_name,
                _row_num,
                ["psi_g_left", "psi_g_right", "psi_g_bottom", "psi_g_top"],
                [
                    self.phx_construction.frame_left.psi_glazing,
                    self.phx_construction.frame_right.psi_glazing,
                    self.phx_construction.frame_bottom.psi_glazing,
                    self.phx_construction.frame_top.psi_glazing,
                ],
                "W/MK",
            )
        )

        # -- psi-install: average values that share a column (PHPP 10.x → left/right share)
        xl_item_list.extend(
            self._build_averaged_psi_items(
                _sheet_name,
                _row_num,
                ["psi_i_left", "psi_i_right", "psi_i_bottom", "psi_i_top"],
                [
                    self.phx_construction.frame_left.psi_install,
                    self.phx_construction.frame_right.psi_install,
                    self.phx_construction.frame_bottom.psi_install,
                    self.phx_construction.frame_top.psi_install,
                ],
                "W/MK",
            )
        )

        return xl_item_list
