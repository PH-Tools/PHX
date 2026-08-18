from PHX.model import certification, ground
from PHX.model.enums.phi_certification_phpp_10 import PhiCertIHGType as PhiCertIHGType_V10
from PHX.model.enums.phi_certification_phpp_9 import PhiCertIHGType as PhiCertIHGType_V9
import pytest


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


def test_PHICertIHGType_enum_v9():
    
    assert PhiCertIHGType_V9.USER_DETERMINED.value == 1
    assert PhiCertIHGType_V9.STANDARD.value == 2
    assert PhiCertIHGType_V9.RES_CUSTOM.value == 3
    assert PhiCertIHGType_V9.NONRES_CUSTOM.value == 4

    with pytest.raises(ValueError):
        PhiCertIHGType_V9(5)  # Invalid value, should raise ValueError


def test_PHICertIHGType_enum_v10():
    
    assert PhiCertIHGType_V10.USER_DEFINED.value == 1
    assert PhiCertIHGType_V10.STANDARD.value == 2
    assert PhiCertIHGType_V10.RES_CUSTOM.value == 3
    assert PhiCertIHGType_V10.NONRES_CUSTOM.value == 4

    with pytest.raises(ValueError):
        PhiCertIHGType_V10(5)  # Invalid value, should raise ValueError