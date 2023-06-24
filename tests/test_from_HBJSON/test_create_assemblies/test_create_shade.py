from honeybee_energy.construction.window import WindowConstruction
from honeybee_energy.construction.windowshade import WindowConstructionShade
from honeybee_energy.material.shade import EnergyWindowMaterialShade
from honeybee_energy.material.glazing import EnergyWindowMaterialSimpleGlazSys

from PHX.from_HBJSON.create_assemblies import (
    build_phx_shade_type_from_HB_WindowConstructionShade,
)


def test_create_phx_shade_from_hb_shade():
    # Create a Shade Material
    shade_material = EnergyWindowMaterialShade(
        identifier="Test Identifier",
        thickness=0.01,
        solar_transmittance=0.34,
    )
    shade_material.display_name = "Test Display Name"

    # Create a mock HBE-WindowConstructionShade object
    hb_const = WindowConstructionShade(
        "test_window_construction_shade",
        window_construction=WindowConstruction(
            identifier="test_window_construction",
            materials=[
                EnergyWindowMaterialSimpleGlazSys(
                    identifier="test_glazing_mat",
                    u_factor=1.0,
                    shgc=0.5,
                )
            ],
        ),
        shade_material=shade_material,
    )

    # Call the method and check the result
    phx_shade = build_phx_shade_type_from_HB_WindowConstructionShade(hb_const)
    assert phx_shade.display_name == "Test Display Name"
    assert phx_shade.identifier == "Test Identifier"
    assert phx_shade.reduction_factor == 0.34
