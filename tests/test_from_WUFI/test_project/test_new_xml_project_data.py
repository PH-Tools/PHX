from PHX.model.project import PhxProject


def test_project_data(
    phx_project_from_hbjson: PhxProject,
    phx_project_from_wufi_xml: PhxProject,
) -> None:
    # -- Pull out the Project Data
    proj_data_hbjson = phx_project_from_hbjson.project_data
    proj_data_xml = phx_project_from_wufi_xml.project_data

    # -- Check the two
    assert proj_data_hbjson.customer == proj_data_xml.customer
    assert proj_data_hbjson.building == proj_data_xml.building
    assert proj_data_hbjson.owner == proj_data_xml.owner
    assert proj_data_hbjson.designer == proj_data_xml.designer
