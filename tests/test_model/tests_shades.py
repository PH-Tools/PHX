from PHX.model.shades import PhxWindowShade

def test_default_PhxWindowShade():
    s1 = PhxWindowShade()
    s2 = PhxWindowShade()

    assert s1 != s2
    assert s1.id_num != s2.id_num