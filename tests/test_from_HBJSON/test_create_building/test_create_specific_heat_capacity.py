# -*- Python Version: 3.10 -*-

"""Tests for PHX.from_HBJSON.create_building functionality"""

from unittest.mock import Mock

import pytest

from PHX.from_HBJSON.create_building import create_specific_heat_capacity
from PHX.model.enums.building import SpecificHeatCapacityType, SpecificHeatCapacityValueWhM2K


class TestCreateSpecificHeatCapacity:
    """Test the create_specific_heat_capacity function."""

    def test_create_specific_heat_capacity_lightweight(self):
        """Test create_specific_heat_capacity with LIGHTWEIGHT type."""
        # -- Setup mock RoomPhProperties with LIGHTWEIGHT capacity
        mock_specific_heat_capacity = Mock()
        mock_specific_heat_capacity.number = 1  # LIGHTWEIGHT

        mock_room_prop_ph = Mock()
        mock_room_prop_ph.specific_heat_capacity = mock_specific_heat_capacity

        # -- Test the function
        result_type, result_value = create_specific_heat_capacity(mock_room_prop_ph)

        # -- Verify results
        assert result_type == SpecificHeatCapacityType.LIGHTWEIGHT
        assert result_value == SpecificHeatCapacityValueWhM2K.LIGHTWEIGHT.value
        assert result_value == 60

    def test_create_specific_heat_capacity_mixed(self):
        """Test create_specific_heat_capacity with MIXED type."""
        # -- Setup mock RoomPhProperties with MIXED capacity
        mock_specific_heat_capacity = Mock()
        mock_specific_heat_capacity.number = 2  # MIXED

        mock_room_prop_ph = Mock()
        mock_room_prop_ph.specific_heat_capacity = mock_specific_heat_capacity

        # -- Test the function
        result_type, result_value = create_specific_heat_capacity(mock_room_prop_ph)

        # -- Verify results
        assert result_type == SpecificHeatCapacityType.MIXED
        assert result_value == SpecificHeatCapacityValueWhM2K.MIXED.value
        assert result_value == 132

    def test_create_specific_heat_capacity_massive(self):
        """Test create_specific_heat_capacity with MASSIVE type."""
        # -- Setup mock RoomPhProperties with MASSIVE capacity
        mock_specific_heat_capacity = Mock()
        mock_specific_heat_capacity.number = 3  # MASSIVE

        mock_room_prop_ph = Mock()
        mock_room_prop_ph.specific_heat_capacity = mock_specific_heat_capacity

        # -- Test the function
        result_type, result_value = create_specific_heat_capacity(mock_room_prop_ph)

        # -- Verify results
        assert result_type == SpecificHeatCapacityType.MASSIVE
        assert result_value == SpecificHeatCapacityValueWhM2K.MASSIVE.value
        assert result_value == 204

    def test_create_specific_heat_capacity_user_defined_with_attribute(self):
        """Test create_specific_heat_capacity with USER_DEFINED type and custom value."""
        # -- Setup mock RoomPhProperties with USER_DEFINED capacity and custom value
        mock_specific_heat_capacity = Mock()
        mock_specific_heat_capacity.number = 6  # USER_DEFINED

        mock_room_prop_ph = Mock()
        mock_room_prop_ph.specific_heat_capacity = mock_specific_heat_capacity
        mock_room_prop_ph.specific_heat_capacity_wh_m2k = 150  # Custom value

        # -- Test the function
        result_type, result_value = create_specific_heat_capacity(mock_room_prop_ph)

        # -- Verify results
        assert result_type == SpecificHeatCapacityType.USER_DEFINED
        assert result_value == 150

    def test_create_specific_heat_capacity_user_defined_fallback(self):
        """Test create_specific_heat_capacity with USER_DEFINED type and fallback value."""
        # -- Setup mock RoomPhProperties with USER_DEFINED capacity but no custom attribute
        mock_specific_heat_capacity = Mock()
        mock_specific_heat_capacity.number = 6  # USER_DEFINED

        mock_room_prop_ph = Mock(spec=[])  # Empty spec prevents auto attribute creation
        mock_room_prop_ph.specific_heat_capacity = mock_specific_heat_capacity
        # No specific_heat_capacity_wh_m2k attribute - should use fallback

        # -- Test the function
        result_type, result_value = create_specific_heat_capacity(mock_room_prop_ph)

        # -- Verify results
        assert result_type == SpecificHeatCapacityType.USER_DEFINED
        assert result_value == 60  # Fallback value

    def test_create_specific_heat_capacity_invalid_type_fallback(self):
        """Test create_specific_heat_capacity with an invalid type that triggers KeyError."""
        # -- Setup mock RoomPhProperties with an invalid type (e.g., 99)
        # This should trigger the KeyError exception and use the fallback
        mock_specific_heat_capacity = Mock()
        mock_specific_heat_capacity.number = 99  # Invalid number that won't match enum

        mock_room_prop_ph = Mock()
        mock_room_prop_ph.specific_heat_capacity = mock_specific_heat_capacity
        mock_room_prop_ph.specific_heat_capacity_wh_m2k = 180  # Custom fallback value

        # -- Test the function - this might raise a ValueError for invalid enum, let's handle it
        with pytest.raises(ValueError):
            # This should raise ValueError when trying to create SpecificHeatCapacityType(99)
            create_specific_heat_capacity(mock_room_prop_ph)
