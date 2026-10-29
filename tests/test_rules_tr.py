"""Data-integrity tests for the Turkish rule module."""

import re

import textscope.rules_tr as rules

# Turkish words that must keep their special letters in the source data.
SPELLED_WORDS = {
    "kapsamlı": "kapsamli",
    "sürdürülebilir": "surdurulebilir",
    "literatür": "literatur",
}


def test_minimum_table_sizes():
    assert len(rules.WORD_SWAPS_TR) >= 450
    assert len(rules.PHRASE_SWAPS_TR) >= 300
    assert len(rules.LEADING_TRANSITIONS_TR) >= 110
    assert len(rules.WORD_VARIANTS_TR) >= 45
    assert len(rules.EXTRA_WORD_SWAPS_TR) >= 90
    assert len(rules.TR_STOPWORDS) >= 200


def test_no_duplicate_word_keys():
    keys = [k for k, _ in rules._WORD_PAIRS_TR]
    assert len(keys) == len(set(keys))


def test_every_regex_compiles():
    for pattern, _ in rules.PHRASE_SWAPS_TR:
        re.compile(pattern)


def test_no_noop_or_empty_swaps():
    for table in (rules.WORD_SWAPS_TR, rules.EXTRA_WORD_SWAPS_TR):
        for key, value in table.items():
            assert key, "empty key"
            assert value, f"empty value for {key!r}"
            assert key != value, f"no-op swap for {key!r}"


def test_keys_are_lowercase():
    for key in rules.WORD_SWAPS_TR:
        assert key == key.lower(), key
        assert key == key.strip(), key


def test_variants_reference_existing_keys():
    for key, variants in rules.WORD_VARIANTS_TR.items():
        assert key in rules.WORD_SWAPS_TR, key
        assert variants, key
        assert len(set(variants)) == len(variants), key


def test_stopwords_are_lowercase():
    for word in rules.TR_STOPWORDS:
        assert word == word.lower(), word
        assert word == word.strip(), word
        assert " " not in word, word


def test_correct_turkish_spelling_in_keys():
    for proper, ascii_version in SPELLED_WORDS.items():
        assert proper in rules.WORD_SWAPS_TR, proper
        assert ascii_version not in rules.WORD_SWAPS_TR, ascii_version


def test_no_double_spaces_in_replacements():
    for table in (rules.WORD_SWAPS_TR, rules.EXTRA_WORD_SWAPS_TR):
        for value in table.values():
            assert "  " not in value, value
    for _, replacement in rules.PHRASE_SWAPS_TR:
        assert "  " not in replacement, replacement


def test_contractions_table_is_empty_for_turkish():
    assert rules.CONTRACTIONS_TR == []


def test_no_circular_single_pass_pairs():
    """A -> B and B -> A in the same table would make output unstable."""
    swaps = rules.WORD_SWAPS_TR
    circular = [
        (a, b) for a, b in swaps.items()
        if swaps.get(b) == a
    ]
    assert circular == [], circular


def test_variant_values_are_not_swap_keys():
    offenders = {
        key: [
            v for v in variants
            if v in rules.WORD_SWAPS_TR or v in rules.EXTRA_WORD_SWAPS_TR
        ]
        for key, variants in rules.WORD_VARIANTS_TR.items()
    }
    offenders = {k: v for k, v in offenders.items() if v}
    assert offenders == {}, offenders


def test_light_verb_nouns_are_not_swapped_bare():
    """'analiz etmek' must not become 'inceleme etmek'."""
    for noun in ("analiz", "yöntem"):
        assert noun not in rules.WORD_SWAPS_TR, noun


# Terms of art: replacing them would change the statistical meaning of a text.
PROTECTED_STAT_TERMS = (
    "anlamlı",
    "istatistiksel",
    "değişken",
    "örneklem",
    "güvenirlik",
    "geçerlik",
    "regresyon",
    "katsayı",
    "p değeri",
    "etki büyüklüğü",
)


def test_protected_statistical_terms_are_not_swapped():
    for term in PROTECTED_STAT_TERMS:
        assert term not in rules.WORD_SWAPS_TR, term
        assert term not in rules.EXTRA_WORD_SWAPS_TR, term


def test_phrase_replacements_are_clean():
    for pattern, replacement in rules.PHRASE_SWAPS_TR:
        assert replacement, pattern
        assert replacement == replacement.strip(), pattern
        assert "  " not in replacement, pattern
        # backreferences would make the replacement depend on the match
        assert not re.search(r"\\[1-9]|\\g<", replacement), pattern


def test_phrase_patterns_use_word_boundaries():
    for pattern, _ in rules.PHRASE_SWAPS_TR:
        assert r"\b" in pattern, pattern


def test_leading_transitions_are_clean():
    for transition in rules.LEADING_TRANSITIONS_TR:
        assert transition, transition
        assert transition == transition.strip(), transition
        assert transition == transition.lower(), transition
        assert "  " not in transition, transition


def test_no_leading_transition_duplicates():
    assert len(rules.LEADING_TRANSITIONS_TR) == len(set(rules.LEADING_TRANSITIONS_TR))
