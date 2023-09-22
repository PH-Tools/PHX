from PHX.model import spaces


def test_default_room_ventilation(reset_class_counters):
    rm_vent_1 = spaces.PhxSpace()
    rm_vent_2 = spaces.PhxSpace()

    assert rm_vent_1 != rm_vent_2
    assert rm_vent_1.id_num == 1
    assert rm_vent_2.id_num == 2


def test_space_no_vent(reset_class_counters) -> None:
    rm_vent_1 = spaces.PhxSpace()
    rm_vent_1.ventilation.load.flow_extract = 0
    rm_vent_1.ventilation.load.flow_supply = 0
    rm_vent_1.ventilation.load.flow_transfer = 0
    assert rm_vent_1.has_ventilation_airflow == False

    rm_vent_2 = spaces.PhxSpace()
    rm_vent_2.ventilation.load.flow_extract = 1
    rm_vent_2.ventilation.load.flow_supply = 1
    rm_vent_2.ventilation.load.flow_transfer = 1
    assert rm_vent_2.has_ventilation_airflow == True
