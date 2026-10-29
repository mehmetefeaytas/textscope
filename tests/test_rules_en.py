"""Data-integrity tests for the English rule module."""

import re

import textscope.rules_en as rules

TURKISH_CHARS = set("çğıöşüÇĞİÖŞÜ")


def test_minimum_table_sizes():
    assert len(rules.WORD_SWAPS_EN) >= 400
    assert len(rules.PHRASE_SWAPS_EN) >= 120
    assert len(rules.LEADING_TRANSITIONS_EN) >= 60
    assert len(rules.CONTRACTIONS_EN) >= 60
    assert len(rules.WORD_VARIANTS_EN) >= 25
    assert len(rules.EXTRA_WORD_SWAPS_EN) >= 40
    assert len(rules.EXTRA_PHRASE_SWAPS_EN) >= 15


def test_no_duplicate_word_keys():
    keys = [k for k, _ in rules._WORD_PAIRS_EN]
    assert len(keys) == len(set(keys))


def test_every_regex_compiles():
    patterns = (
        rules.PHRASE_SWAPS_EN
        + rules.CONTRACTIONS_EN
        + rules.EXTRA_PHRASE_SWAPS_EN
    )
    for pattern, _ in patterns:
        re.compile(pattern)


def test_no_noop_or_empty_swaps():
    for table in (rules.WORD_SWAPS_EN, rules.EXTRA_WORD_SWAPS_EN):
        for key, value in table.items():
            assert key, "empty key"
            assert value, f"empty value for {key!r}"
            assert key != value, f"no-op swap for {key!r}"


def test_keys_are_lowercase_and_stripped():
    for key in rules.WORD_SWAPS_EN:
        assert key == key.lower(), key
        assert key == key.strip(), key
    for key in rules.EXTRA_WORD_SWAPS_EN:
        assert key == key.lower(), key


def test_variants_reference_existing_keys():
    for key, variants in rules.WORD_VARIANTS_EN.items():
        assert key in rules.WORD_SWAPS_EN, key
        assert variants, key
        assert len(set(variants)) == len(variants), key
        for variant in variants:
            assert variant and variant == variant.strip()


def test_no_turkish_characters():
    for key, value in rules.WORD_SWAPS_EN.items():
        assert not (set(key) | set(value)) & TURKISH_CHARS, key


def test_transitions_are_lowercase_single_line():
    for transition in rules.LEADING_TRANSITIONS_EN:
        assert transition == transition.lower()
        assert "\n" not in transition
        assert transition == transition.strip()


def test_phrase_replacements_have_no_backreferences():
    for pattern, replacement in rules.PHRASE_SWAPS_EN:
        assert "\\1" not in replacement
        assert "\\g<" not in replacement


def test_replacement_lists_are_pairs():
    for table in (rules.PHRASE_SWAPS_EN, rules.CONTRACTIONS_EN):
        for item in table:
            assert len(item) == 2, item
            assert all(isinstance(part, str) for part in item)


def test_variant_values_are_not_swap_keys():
    """A variant that is itself a key creates non-idempotent chains."""
    offenders = {
        key: [v for v in variants if v in rules.WORD_SWAPS_EN]
        for key, variants in rules.WORD_VARIANTS_EN.items()
    }
    offenders = {k: v for k, v in offenders.items() if v}
    assert offenders == {}, offenders


def test_aggressive_extras_are_meaningful():
    """Extras either add new keys or deliberately override for a stronger tone."""
    redundant = {
        key: value
        for key, value in rules.EXTRA_WORD_SWAPS_EN.items()
        if rules.WORD_SWAPS_EN.get(key) == value
    }
    assert redundant == {}, redundant
