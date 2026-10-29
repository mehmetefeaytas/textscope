from textscope.clean import clean_text


def test_zero_width_removed():
    assert "\u200b" not in clean_text("a\u200bb")


def test_ligature():
    assert clean_text("\ufb01le") == "file"


def test_idempotent():
    t = "Hello   world.\n\n\n\nEnd."
    once = clean_text(t)
    twice = clean_text(once)
    assert once == twice


def test_protected_number_preserved():
    t = "Value is 42 here."
    out = clean_text(t)
    assert "42" in out
