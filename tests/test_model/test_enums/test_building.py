# -*- Python Version: 3.10 -*-

"""Tests for PHX.model.enums.building"""

import pytest

from PHX.model.enums.building import (
    ComponentExposureExterior,
    ComponentFaceType,
    SpecificHeatCapacityType,
    SpecificHeatCapacityValueWhM2K,
)


class TestComponentFaceType:
    def test_air_boundary_is_distinct_from_roof_ceiling(self):
        assert ComponentFaceType.AIR_BOUNDARY is not ComponentFaceType.ROOF_CEILING

    def test_air_boundary_value(self):
        assert ComponentFaceType.AIR_BOUNDARY.value == 7

    def test_air_boundary_name(self):
        assert ComponentFaceType.AIR_BOUNDARY.name == "AIR_BOUNDARY"

    def test_air_boundary_in_iteration(self):
        names = {m.name for m in ComponentFaceType}
        assert "AIR_BOUNDARY" in names

    def test_all_values_unique(self):
        values = [m.value for m in ComponentFaceType]
        assert len(values) == len(set(values))

    def test_existing_values_unchanged(self):
        assert ComponentFaceType.NONE.value == 0
        assert ComponentFaceType.WALL.value == 1
        assert ComponentFaceType.FLOOR.value == 2
        assert ComponentFaceType.ROOF_CEILING.value == 3
        assert ComponentFaceType.WINDOW.value == 4
        assert ComponentFaceType.ADIABATIC.value == 5
        assert ComponentFaceType.CUSTOM.value == 6

    def test_lookup_by_value_7(self):
        assert ComponentFaceType(7) is ComponentFaceType.AIR_BOUNDARY


class TestComponentExposureExterior:
    def test_known_members(self):
        assert ComponentExposureExterior.EXTERIOR.value == -1
        assert ComponentExposureExterior.GROUND.value == -2
        assert ComponentExposureExterior.SURFACE.value == -3

    def test_zone_id_pseudo_member_from_int(self):
        z3 = ComponentExposureExterior(3)
        assert z3.value == 3
        assert z3.name == "ZONE_3"
        assert ComponentExposureExterior(3) is z3

    def test_zone_id_pseudo_member_from_digit_string(self):
        z7 = ComponentExposureExterior("7")
        assert z7.value == 7
        assert z7.name == "ZONE_7"

    def test_unknown_negative_value_raises(self):
        with pytest.raises(ValueError):
            ComponentExposureExterior(-99)


class TestSpecificHeatCapacityValueWhM2K:
    """Test the SpecificHeatCapacityValueWhM2K enum."""

    def test_lightweight_value(self):
        """Test that LIGHTWEIGHT has the correct Wh/m²K value."""
        assert SpecificHeatCapacityValueWhM2K.LIGHTWEIGHT.value == 60

    def test_mixed_value(self):
        """Test that MIXED has the correct Wh/m²K value."""
        assert SpecificHeatCapacityValueWhM2K.MIXED.value == 132

    def test_massive_value(self):
        """Test that MASSIVE has the correct Wh/m²K value."""
        assert SpecificHeatCapacityValueWhM2K.MASSIVE.value == 204

    def test_all_enum_members_exist(self):
        """Test that all expected enum members are present."""
        expected_members = {"LIGHTWEIGHT", "MIXED", "MASSIVE"}
        actual_members = {member.name for member in SpecificHeatCapacityValueWhM2K}
        assert actual_members == expected_members

    def test_enum_correspondence_with_specific_heat_capacity_type(self):
        """Test that SpecificHeatCapacityValueWhM2K members correspond to SpecificHeatCapacityType names."""
        # This tests the relationship used in create_specific_heat_capacity function

        # Test LIGHTWEIGHT correspondence
        type_enum = SpecificHeatCapacityType.LIGHTWEIGHT
        value_enum = SpecificHeatCapacityValueWhM2K[type_enum.name]
        assert value_enum == SpecificHeatCapacityValueWhM2K.LIGHTWEIGHT
        assert value_enum.value == 60

        # Test MIXED correspondence
        type_enum = SpecificHeatCapacityType.MIXED
        value_enum = SpecificHeatCapacityValueWhM2K[type_enum.name]
        assert value_enum == SpecificHeatCapacityValueWhM2K.MIXED
        assert value_enum.value == 132

        # Test MASSIVE correspondence
        type_enum = SpecificHeatCapacityType.MASSIVE
        value_enum = SpecificHeatCapacityValueWhM2K[type_enum.name]
        assert value_enum == SpecificHeatCapacityValueWhM2K.MASSIVE
        assert value_enum.value == 204

    def test_user_defined_has_no_corresponding_value_enum(self):
        """Test that USER_DEFINED type has no corresponding value enum (expected KeyError)."""
        type_enum = SpecificHeatCapacityType.USER_DEFINED

        # This should raise KeyError as USER_DEFINED is not in SpecificHeatCapacityValueWhM2K
        with pytest.raises(KeyError):
            SpecificHeatCapacityValueWhM2K[type_enum.name]


class TestSpecificHeatCapacityType:
    """Test the SpecificHeatCapacityType enum for completeness."""

    def test_enum_values(self):
        """Test that SpecificHeatCapacityType has the expected values."""
        assert SpecificHeatCapacityType.LIGHTWEIGHT.value == 1
        assert SpecificHeatCapacityType.MIXED.value == 2
        assert SpecificHeatCapacityType.MASSIVE.value == 3
        assert SpecificHeatCapacityType.USER_DEFINED.value == 6

    def test_all_enum_members_exist(self):
        """Test that all expected enum members are present."""
        expected_members = {"LIGHTWEIGHT", "MIXED", "MASSIVE", "USER_DEFINED"}
        actual_members = {member.name for member in SpecificHeatCapacityType}
        assert actual_members == expected_members
