# -*- coding: utf-8 -*-
# -*- Python Version: 3.7 -*-

"""PHX Collection class for Organizing Space Schedules as Utilization Patterns."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Union, Dict, Optional
import uuid

from PHX.model.schedules.ventilation import PhxScheduleVentilation
from PHX.model.schedules.occupancy import PhxScheduleOccupancy


@dataclass
class UtilizationPatternCollection_Ventilation:
    patterns: Dict[Union[str, uuid.UUID], PhxScheduleVentilation] = field(
        init=False, default_factory=dict
    )

    def __getitem__(self, key) -> PhxScheduleVentilation:
        return self.patterns[key]

    def __setitem__(
        self, key: Union[str, uuid.UUID], value: PhxScheduleVentilation
    ) -> None:
        self.patterns[key] = value

    def add_new_util_pattern(
        self, _util_pattern: Optional[PhxScheduleVentilation]
    ) -> None:
        """Add a new PhxScheduleVentilation to the Collection.

        Arguments:
        ----------
            * _util_pattern (PhxScheduleVentilation): The PhxScheduleVentilation
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

    def get_pattern_by_id_num(self, _id_num: int) -> PhxScheduleVentilation:
        """Return a PhxScheduleVentilation from the collection found by an id-num

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
        msg = f"Error: Cannot locate the PhxScheduleVentilation with id-number: {_id_num}"
        raise Exception(msg)

    def __len__(self):
        return len(self.patterns.keys())

    def __iter__(self):
        for v in self.patterns.values():
            yield v

    def __bool__(self):
        return bool(self.patterns)

    def items(self):
        return self.patterns.items()

    def keys(self):
        return self.patterns.keys()

    def values(self):
        return self.patterns.values()


@dataclass
class UtilizationPatternCollection_Occupancy:
    patterns: Dict[Union[str, uuid.UUID], PhxScheduleOccupancy] = field(
        init=False, default_factory=dict
    )

    def __getitem__(self, key) -> PhxScheduleOccupancy:
        return self.patterns[key]

    def __setitem__(
        self, key: Union[str, uuid.UUID], value: PhxScheduleOccupancy
    ) -> None:
        self.patterns[key] = value

    def add_new_util_pattern(self, _util_pattern: Optional[PhxScheduleOccupancy]) -> None:
        """Add a new PhxScheduleOccupancy to the Collection.

        Arguments:
        ----------
            * _util_pattern (Optional[PhxScheduleOccupancy]): The PhxScheduleOccupancy
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

    def get_pattern_by_id_num(self, _id_num: int) -> PhxScheduleOccupancy:
        """Return a PhxScheduleOccupancy from the collection found by an id-num

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
        msg = f"Error: Cannot locate the PhxScheduleOccupancy with id-number: {_id_num}"
        raise Exception(msg)

    def __len__(self):
        return len(self.patterns.keys())

    def __iter__(self):
        for v in self.patterns.values():
            yield v

    def __bool__(self):
        return bool(self.patterns)

    def items(self):
        return self.patterns.items()

    def keys(self):
        return self.patterns.keys()

    def values(self):
        return self.patterns.values()
