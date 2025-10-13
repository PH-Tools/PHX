# -*- coding: utf-8 -*-
# -*- Python Version: 3.10 -*-

"""Tests for PHX.model.enums.building"""

import pytest

from PHX.model.enums.building import SpecificHeatCapacityType, SpecificHeatCapacityValueWhM2K


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
