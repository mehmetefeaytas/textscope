from textscope.clean import clean_text
from textscope.protected import verify_protected


def test_clean_protected_preserved():
    text = "Prose with 42 and https://x.com and \\cite{a}."
    out = clean_text(text)
    ok, errs = verify_protected(text, out)
    assert ok, errs


def test_clean_idempotent():
    t = "Hello   world.\u200b\n\n\n\nEnd \u2014 test."
    assert clean_text(clean_text(t)) == clean_text(t)
