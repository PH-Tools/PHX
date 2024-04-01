from PHX.model.enums.phx_site import SiteEnergyFactorSelection
from PHX.model.project import PhxProject


def test_CO2_Factors(phx_project_from_wufi_xml_SCHOOL: PhxProject) -> None:
    assert True

    # -- Check the PE Factors match the expected values - this model uses Standard-USA
    factors = phx_project_from_wufi_xml_SCHOOL.variants[0].site.energy_factors
    assert factors.selection_pe_co2_factor == SiteEnergyFactorSelection.STANDARD_USA
    assert len(factors.co2_factors) == 16
