# -*- Python Version: 3.10 -*-

"""Shared test helpers for construction tests."""

from PHX.model.constructions import PhxLayer, PhxMaterial


def make_test_layer(thickness_m: float, conductivity: float, display_name: str = "") -> PhxLayer:
    """Create a simple single-material PhxLayer (no division grid)."""
    mat = PhxMaterial(display_name=display_name)
    mat.conductivity = conductivity
    layer = PhxLayer()
    layer.thickness_m = thickness_m
    layer.set_material(mat)
    return layer
