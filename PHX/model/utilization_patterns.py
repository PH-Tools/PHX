# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""PHX Collection class for Organizing Space Schedules as Utilization Patterns."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Generator, ItemsView, KeysView, Optional, Union, ValuesView

from PHX.model.schedules import lighting, occupancy, ventilation


@dataclass
class UtilizationPatternCollection_Ventilation:
    patterns: Dict[Union[str, uuid.UUID], ventilation.PhxScheduleVentilation] = field(init=False, default_factory=dict)

    def __getitem__(self, key) -> ventilation.PhxScheduleVentilation:
        return self.patterns[key]

    def __setitem__(self, key: Union[str, uuid.UUID], value: ventilation.PhxScheduleVentilation) -> None:
        self.patterns[key] = value

    def add_new_util_pattern(self, _util_pattern: Optional[ventilation.PhxScheduleVentilation]) -> None:
        """Add a new ventilation.PhxScheduleVentilation to the Collection.

        Arguments:
        ----------
            * _util_pattern (ventilation.PhxScheduleVentilation): The ventilation.PhxScheduleVentilation
                pattern to add to the collection.

        Returns:
        --------
            * None
        """
        if _util_pattern is None:
            return

        self.patterns[_util_pattern.identifier] = _util_pattern

    def key_is_in_collection(self, _id) -> bool:
        """Check if the id is in the collection."""
        return _id in self.patterns.keys()

    def get_pattern_by_id_num(self, _id_num: int) -> ventilation.PhxScheduleVentilation:
        """Return a ventilation.PhxScheduleVentilation from the collection found by an id-num

        Arguments:
        ----------
            * _id_num (int): The id-number of the Schedule to find.

        Returns:
        --------
            * None
        """
        for pattern in self.patterns.values():
            if pattern.id_num == _id_num:
                return pattern
        msg = f"Error: Cannot locate the ventilation.PhxScheduleVentilation with id-number: {_id_num}"
        raise Exception(msg)

    def __len__(self) -> int:
        return len(self.patterns.keys())

    def __iter__(self) -> Generator[ventilation.PhxScheduleVentilation, Any, None]:
        for v in self.patterns.values():
            yield v

    def __bool__(self) -> bool:
        return bool(self.patterns)

    def items(self) -> ItemsView:
        return self.patterns.items()

    def keys(self) -> KeysView:
        return self.patterns.keys()

    def values(self) -> ValuesView:
        return self.patterns.values()


@dataclass
class UtilizationPatternCollection_Occupancy:
    patterns: Dict[Union[str, uuid.UUID], occupancy.PhxScheduleOccupancy] = field(init=False, default_factory=dict)

    def __getitem__(self, key) -> occupancy.PhxScheduleOccupancy:
        return self.patterns[key]

    def __setitem__(self, key: Union[str, uuid.UUID], value: occupancy.PhxScheduleOccupancy) -> None:
        self.patterns[key] = value

    def add_new_util_pattern(self, _util_pattern: Optional[occupancy.PhxScheduleOccupancy]) -> None:
        """Add a new occupancy.PhxScheduleOccupancy to the Collection.

        Arguments:
        ----------
            * _util_pattern (Optional[occupancy.PhxScheduleOccupancy]): The occupancy.PhxScheduleOccupancy
                pattern to add to the collection.

        Returns:
        --------
            * None
        """
        if _util_pattern is None:
            return

        self.patterns[_util_pattern.identifier] = _util_pattern

    def key_is_in_collection(self, _id: Union[str, uuid.UUID]) -> bool:
        """Check if the id is in the collection."""
        return _id in self.patterns.keys()

    def get_pattern_by_id_num(self, _id_num: int) -> occupancy.PhxScheduleOccupancy:
        """Return a occupancy.PhxScheduleOccupancy from the collection found by an id-num

        Arguments:
        ----------
            * _id_num (int): The id-number of the Schedule to find.

        Returns:
        --------
            * None
        """
        for pattern in self.patterns.values():
            if pattern.id_num == _id_num:
                return pattern
        msg = f"Error: Cannot locate the occupancy.PhxScheduleOccupancy with id-number: {_id_num}"
        raise Exception(msg)

    def __len__(self) -> int:
        return len(self.patterns.keys())

    def __iter__(self) -> Generator[occupancy.PhxScheduleOccupancy, Any, None]:
        for v in self.patterns.values():
            yield v

    def __bool__(self) -> bool:
        return bool(self.patterns)

    def items(self):
        return self.patterns.items()

    def keys(self):
        return self.patterns.keys()

    def values(self):
        return self.patterns.values()


@dataclass
class UtilizationPatternCollection_Lighting:
    patterns: Dict[Union[str, uuid.UUID], lighting.PhxScheduleLighting] = field(init=False, default_factory=dict)

    def __getitem__(self, key) -> lighting.PhxScheduleLighting:
        return self.patterns[key]

    def __setitem__(self, key: Union[str, uuid.UUID], value: lighting.PhxScheduleLighting) -> None:
        self.patterns[key] = value

    def add_new_util_pattern(self, _util_pattern: Optional[lighting.PhxScheduleLighting]) -> None:
        """Add a new lighting.PhxScheduleLighting to the Collection.

        Arguments:
        ----------
            * _util_pattern (Optional[lighting.PhxScheduleLighting]): The lighting.PhxScheduleLighting
                pattern to add to the collection.

        Returns:
        --------
            * None
        """
        if _util_pattern is None:
            return

        self.patterns[_util_pattern.identifier] = _util_pattern

    def key_is_in_collection(self, _id) -> bool:
        """Check if the id is in the collection."""
        return _id in self.patterns.keys()

    def get_pattern_by_id_num(self, _id_num: int) -> lighting.PhxScheduleLighting:
        """Return a lighting.PhxScheduleLighting from the collection found by an id-num

        Arguments:
        ----------
            * _id_num (int): The id-number of the Schedule to find.

        Returns:
        --------
            * None
        """
        for pattern in self.patterns.values():
            if pattern.id_num == _id_num:
                return pattern
        msg = f"Error: Cannot locate the lighting.PhxScheduleLighting with id-number: {_id_num}"
        raise Exception(msg)

    def __len__(self) -> int:
        return len(self.patterns.keys())

    def __iter__(self) -> Generator[lighting.PhxScheduleLighting, Any, None]:
        for v in self.patterns.values():
            yield v

    def __bool__(self) -> bool:
        return bool(self.patterns)

    def items(self):
        return self.patterns.items()

    def keys(self):
        return self.patterns.keys()

    def values(self):
        return self.patterns.values()
