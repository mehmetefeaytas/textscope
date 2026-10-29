from textscope.rewrite import rewrite_text


def test_strict_word_count():
    text = "Moreover, it is important to note that AI is pivotal. Furthermore, we utilize robust frameworks."
    out = rewrite_text(text, strict=True)
    assert len(out.split()) == len(text.split())


def test_protected_preserved():
    text = "Hello world with 42 and https://example.com and \\cite{foo}."
    out = rewrite_text(text, strict=False)
    assert "42" in out
    assert "https://example.com" in out
    assert "\\cite{foo}" in out


def test_idempotent_ish():
    text = "Moreover, AI is pivotal."
    out1 = rewrite_text(text, strict=False)
    out2 = rewrite_text(out1, strict=False)
    # not necessarily identical but should not crash; protected not relevant
    assert isinstance(out2, str)


def test_verify_protected_after_rewrite():
    from textscope.protected import verify_protected
    text = "Hello 42 https://x.com and \\cite{a}."
    out = rewrite_text(text, strict=True)
    ok, errs = verify_protected(text, out)
    assert ok, errs


def test_property_protected_preserved_random():
    from textscope.protected import verify_protected
    import random
    base = "Some prose here with 42 and https://example.com and \\cite{ref} and `code`."
    for seed in range(5):
        out = rewrite_text(base, strict=(seed % 2 == 0), seed=seed)
        ok, errs = verify_protected(base, out)
        assert ok, errs


def test_strict_idempotent_wordcount_stability():
    text = "Moreover, this is a test. Furthermore, another sentence here."
    o1 = rewrite_text(text, strict=True)
    assert len(o1.split()) == len(text.split())
