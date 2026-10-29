from textscope.protected import split_protected, verify_protected


def test_protected_preserved():
    text = "Hello world. Number 42 and url https://example.com and cite \\cite{foo} and code `x=1`."
    spans = split_protected(text)
    prot = [s.text for s in spans if s.protected]
    assert "42" in prot
    assert "https://example.com" in prot
    assert "\\cite{foo}" in prot
    assert "`x=1`" in prot


def test_verify_identical():
    text = "Hello 42 https://x.com"
    ok, errs = verify_protected(text, text)
    assert ok
    assert errs == []


def test_verify_changed_fails():
    text = "Hello 42"
    bad = "Hello 43"
    ok, _errs = verify_protected(text, bad)
    assert not ok
