from PHX.model import project, constructions


def test_blank_project(reset_class_counters):
    proj = project.PhxProject()

    assert str(proj)
    assert not proj.assembly_types
    assert not proj.window_types
    assert not proj.utilization_patterns_ventilation
    assert not proj.utilization_patterns_occupancy
    assert not proj.variants


def test_project_data(reset_class_counters):
    proj = project.PhxProject()

    # -- Set all the data
    fields = [
        "name",
        "street",
        "city",
        "post_code",
        "telephone",
        "email",
        "license_number",
    ]
    group_types = ["customer", "building", "owner", "designer"]
    for group_name in group_types:
        gr_attr = getattr(proj.project_data, group_name)
        for field in fields:
            setattr(gr_attr, field, f"{group_name}_{field}")

    # --- Customer
    assert proj.project_data.customer.name == "customer_name"
    assert proj.project_data.customer.street == "customer_street"
    assert proj.project_data.customer.city == "customer_city"
    assert proj.project_data.customer.post_code == "customer_post_code"
    assert proj.project_data.customer.telephone == "customer_telephone"
    assert proj.project_data.customer.email == "customer_email"
    assert proj.project_data.customer.license_number == "customer_license_number"

    # --- Building
    assert proj.project_data.building.name == "building_name"
    assert proj.project_data.building.street == "building_street"
    assert proj.project_data.building.city == "building_city"
    assert proj.project_data.building.post_code == "building_post_code"
    assert proj.project_data.building.telephone == "building_telephone"
    assert proj.project_data.building.email == "building_email"
    assert proj.project_data.building.license_number == "building_license_number"

    # --- Owner
    assert proj.project_data.owner.name == "owner_name"
    assert proj.project_data.owner.street == "owner_street"
    assert proj.project_data.owner.city == "owner_city"
    assert proj.project_data.owner.post_code == "owner_post_code"
    assert proj.project_data.owner.telephone == "owner_telephone"
    assert proj.project_data.owner.email == "owner_email"
    assert proj.project_data.owner.license_number == "owner_license_number"

    # --- Responsible
    assert proj.project_data.designer.name == "designer_name"
    assert proj.project_data.designer.street == "designer_street"
    assert proj.project_data.designer.city == "designer_city"
    assert proj.project_data.designer.post_code == "designer_post_code"
    assert proj.project_data.designer.telephone == "designer_telephone"
    assert proj.project_data.designer.email == "designer_email"
    assert proj.project_data.designer.license_number == "designer_license_number"


def test_add_variant_to_project(reset_class_counters):
    proj = project.PhxProject()

    assert not proj.variants

    var_1 = project.PhxVariant()
    var_2 = project.PhxVariant()

    assert var_1.id_num == 1
    assert var_2.id_num == 2

    proj.add_new_variant(var_1)
    assert len(proj.variants) == 1
    assert var_1 in proj.variants
    assert var_2 not in proj.variants

    proj.add_new_variant(var_2)
    assert len(proj.variants) == 2
    assert var_1 in proj.variants
    assert var_2 in proj.variants


def test_add_assembly_to_project(reset_class_counters):
    pr_1 = project.PhxProject()

    assembly_1 = constructions.PhxConstructionOpaque()
    assembly_2 = constructions.PhxConstructionOpaque()

    pr_1.add_assembly_type(assembly_1)
    assert assembly_1.identifier in pr_1.assembly_types
    assert assembly_2.identifier not in pr_1.assembly_types

    pr_1.add_assembly_type(assembly_2)
    assert assembly_1.identifier in pr_1.assembly_types
    assert assembly_2.identifier in pr_1.assembly_types

    pr_2 = project.PhxProject()
    assert assembly_1.identifier not in pr_2.assembly_types
    assert assembly_2.identifier not in pr_2.assembly_types
