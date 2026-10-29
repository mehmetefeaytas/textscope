"""Regression tests for the idempotency and sentence-splitting bugs.

Both were found by the quality gate in ``tests/test_quality_gate.py``:

* the rewriter was not idempotent because some swap tables contained chains
  (``framework -> structure -> shape``), so a second pass changed the text again;
* the sentence splitter cut at *list* commas and at "and" inside an adjective
  phrase, producing fragments such as ``needs a full. Complex way``.
"""

from textscope.rewrite import (
    _break_chains,
    _looks_like_clause_start,
    rewrite_text,
)

EN_LONG = (
    "In today's increasingly interconnected and rapidly evolving global landscape, "
    "it is critically important to recognize that the successful implementation of "
    "sustainable practices requires a comprehensive and multifaceted approach that "
    "simultaneously addresses economic, environmental, and social considerations."
)

TR_LONG = (
    "Günümüzün giderek karmaşıklaşan ve hızla değişen küresel ortamında, kalıcı "
    "uygulamaların hayata geçirilmesinin ekonomik, çevresel ve toplumsal boyutları "
    "aynı anda ele alan kapsamlı bir yaklaşım gerektirdiğini belirtmek gerekir."
)


# ---------- chain breaking ----------

def test_break_chains_drops_links_to_other_keys():
    swaps = {"a": "b", "b": "c", "x": "y"}
    assert _break_chains(swaps) == {"b": "c", "x": "y"}


def test_break_chains_keeps_independent_pairs():
    swaps = {"utilize": "use", "leverage": "use"}
    assert _break_chains(swaps) == swaps


def test_rewriting_is_idempotent_in_english():
    once = rewrite_text(EN_LONG, lang="en")
    assert rewrite_text(once, lang="en") == once


def test_rewriting_is_idempotent_in_turkish():
    once = rewrite_text(TR_LONG, lang="tr")
    assert rewrite_text(once, lang="tr") == once


def test_rewriting_is_idempotent_for_every_seed():
    for seed in range(6):
        once = rewrite_text(EN_LONG, lang="en", seed=seed)
        assert rewrite_text(once, lang="en", seed=seed) == once, seed


def test_rewriting_is_idempotent_for_every_profile():
    for profile in ("conservative", "balanced", "aggressive"):
        once = rewrite_text(EN_LONG, lang="en", profile=profile)
        assert rewrite_text(once, lang="en", profile=profile) == once, profile


def test_strict_mode_is_idempotent():
    once = rewrite_text(EN_LONG, lang="en", strict=True)
    assert rewrite_text(once, lang="en", strict=True) == once


# ---------- enumeration safety ----------

def test_list_comma_is_not_a_clause_boundary():
    out = rewrite_text(EN_LONG, lang="en")
    assert "economic. Environmental" not in out
    assert "economic, environmental, and social" in out


def test_adjective_conjunction_is_not_a_clause_boundary():
    """'comprehensive and multifaceted approach' must not become a fragment."""
    text = (
        "The successful implementation of sustainable practices requires a "
        "comprehensive and multifaceted approach that addresses local conditions."
    )
    out = rewrite_text(text, lang="en")
    assert ". Complex" not in out
    assert ". Multifaceted" not in out


def test_turkish_list_comma_is_not_a_clause_boundary():
    out = rewrite_text(TR_LONG, lang="tr")
    assert "ekonomik. Çevresel" not in out


def test_real_clause_boundary_still_splits():
    """The guard must not disable splitting altogether."""
    text = (
        "The first survey collected responses from two hundred students, and it "
        "then compared those outcomes with earlier published results."
    )
    out = rewrite_text(text, lang="en")
    assert out.count(". ") >= 1


def test_clause_start_detection():
    assert _looks_like_clause_start("it then compared the data", "en")
    assert _looks_like_clause_start("the data were clear", "en")
    assert not _looks_like_clause_start("complex way that works", "en")
    assert not _looks_like_clause_start("environmental and social", "en")
    assert _looks_like_clause_start("bu durumda sonuç değişir", "tr")


def test_no_dangling_tail_after_split():
    """A split must not leave a fragment ending in a preposition or article."""
    text = (
        "We ran the experiment with a great deal of care and the results were "
        "consistent across every single trial in the study."
    )
    out = rewrite_text(text, lang="en")
    fragments = [f.strip() for f in out.split(". ") if f.strip()]
    for fragment in fragments:
        last = fragment.rsplit(maxsplit=1)[-1].strip(".,;:").lower()
        assert last not in {"of", "in", "on", "at", "for", "to", "with", "and", "the", "a", "an"}, (
            f"fragment ends with a dangling word: {fragment!r}"
        )
    # and the content survived
    assert "experiment" in out
    assert "trial" in out
