from PHX.model import certification, ground
from PHX.model.enums.phi_certification_phpp_10 import PhiCertIHGType as PhiCertIHGType_V10
from PHX.model.enums.phi_certification_phpp_9 import PhiCertIHGType as PhiCertIHGType_V9
import pytest
import json
from pathlib import Path


def test_default_PH_Building(reset_class_counters):
    obj_1 = certification.PhxPhBuildingData()
    assert obj_1.id_num == 1
    obj_2 = certification.PhxPhBuildingData()
    assert obj_2.id_num == 2

    assert id(obj_1) != id(obj_2)
    assert not obj_1.foundations
    assert not obj_2.foundations


def test_add_single_foundation(reset_class_counters):
    obj_1 = certification.PhxPhBuildingData()
    f_1 = ground.PhxFoundation()
    obj_1.add_foundation(f_1)

    assert len(obj_1.foundations) == 1
    assert f_1 in obj_1.foundations


IHG_ENUM_BY_VERSION = {"9": PhiCertIHGType_V9, "10": PhiCertIHGType_V10}

LOCALIZATION_DIR = Path(__file__).parents[3] / "PHX" / "PHPP" / "phpp_localization"
JSON_PATHS = sorted(LOCALIZATION_DIR.glob("*.json"))


@pytest.mark.parametrize("json_path", sorted(Path("PHX/PHPP/phpp_localization").glob("*.json")))
def test_ihg_options_cover_the_enum(json_path):
    enum_cls = IHG_ENUM_BY_VERSION[json_path.stem.split("_")[1]]
    options = json.loads(json_path.read_text())["VERIFICATION"]["phi_building_ihg_type"]["options"]
    assert {str(m.value) for m in enum_cls} == set(options)
    assert JSON_PATHS, "no localization files found at {}".format(LOCALIZATION_DIR)  # <--- check we found something
