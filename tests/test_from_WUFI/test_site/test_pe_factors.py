from PHX.model.enums.phx_site import SiteEnergyFactorSelection
from PHX.model.project import PhxProject


def test_PE_Factors_School(phx_project_from_wufi_xml_SCHOOL: PhxProject) -> None:
    assert True

    # -- Check the PE Factors match the expected values - this model uses Standard-USA
    factors = phx_project_from_wufi_xml_SCHOOL.variants[0].site.energy_factors
    assert factors.selection_pe_co2_factor == SiteEnergyFactorSelection.STANDARD_USA
    assert len(factors.pe_factors) == 16
    assert factors.pe_factors["ELECTRICITY_MIX"].value == 2.8


def test_PE_Factors_UserDefined(phx_project_from_wufi_xml_RIDGEWAY: PhxProject) -> None:
    assert True

    # -- Check the PE Factors match the expected values - this model uses Standard-USA
    factors = phx_project_from_wufi_xml_RIDGEWAY.variants[0].site.energy_factors
    assert factors.selection_pe_co2_factor == SiteEnergyFactorSelection.USER_DEFINED
    assert len(factors.pe_factors) == 16
    assert factors.pe_factors["ELECTRICITY_MIX"].value == 1.8
