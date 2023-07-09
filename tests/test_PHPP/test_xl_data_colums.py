from PHX.xl import xl_data


def test_xl_ord():
    assert xl_data.xl_ord("A") == ord("A")
    assert xl_data.xl_ord("B") == ord("B")
    assert xl_data.xl_ord("AA") == 91
    assert xl_data.xl_ord("AZ") == 116
    assert xl_data.xl_ord("BA") == 117
    assert xl_data.xl_ord("BZ") == 142


def test_xl_chr():
    assert xl_data.xl_chr(65) == "A"
    assert xl_data.xl_chr(66) == "B"
    assert xl_data.xl_chr(91) == "AA"


def test_xl_chr_equals_xl_ord():
    assert xl_data.xl_chr(xl_data.xl_ord("A")) == "A"
    assert xl_data.xl_chr(xl_data.xl_ord("B")) == "B"
    assert xl_data.xl_chr(xl_data.xl_ord("AA")) == "AA"
    assert xl_data.xl_chr(xl_data.xl_ord("AZ")) == "AZ"
    assert xl_data.xl_chr(xl_data.xl_ord("BT")) == "BT"


def test_col_offset():
    assert xl_data.col_offset("A", 1) == "B"
    assert xl_data.col_offset("A", 2) == "C"
    assert xl_data.col_offset("Z", 1) == "AA"
    assert xl_data.col_offset("Z", 2) == "AB"
    assert xl_data.col_offset("AR", 1) == "AS"
    assert xl_data.col_offset("AR", 2) == "AT"
