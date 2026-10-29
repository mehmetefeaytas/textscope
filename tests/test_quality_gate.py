"""Quality-gate tests for textscope rewrites.

The harness in ``textscope.eval`` rewrites a fixed bilingual corpus and checks
that each output is structurally intact, meaning-preserving, language-stable,
idempotent and free of rewrite artifacts. These tests pin the current baseline
so regressions fail loudly.

The allowlist below is empty: all 27 samples pass all 8 checks. If a future
change breaks the gate, fix the cause instead of adding an entry.
"""

from __future__ import annotations

import pytest

from textscope.eval import EN_CORPUS, TR_CORPUS, evaluate, format_report, run_checks

# Empty on purpose: every sample must pass every check. When this list grows it
# means a real regression, so it should be fixed rather than allowlisted.
KNOWN_FAILURES: dict[tuple[str, str], str] = {}


@pytest.fixture(scope="module")
def report() -> dict:
    return evaluate()


def test_nothing_outside_allowlist_fails(report: dict) -> None:
    unexpected: list[str] = []
    failing: set[tuple[str, str]] = set()
    for row in report["samples"]:
        for check in row["checks"]:
            if check.passed:
                continue
            key = (row["name"], check.name)
            failing.add(key)
            if key not in KNOWN_FAILURES:
                unexpected.append(f"{row['name']} / {check.name}: {check.detail}")
    assert not unexpected, "new quality failures:\n" + "\n".join(unexpected)


def test_format_report_lists_every_sample(report: dict) -> None:
    rendered = format_report(report)
    assert rendered.strip()
    for sample in [*EN_CORPUS, *TR_CORPUS]:
        assert sample.name in rendered, f"report is missing sample {sample.name}"


def test_corpora_have_at_least_twelve_samples() -> None:
    assert len(EN_CORPUS) >= 12
    assert len(TR_CORPUS) >= 12


def _has_match(corpus: list, pattern: str) -> bool:
    return any(pattern in sample.text for sample in corpus)


def test_corpus_covers_protected_and_language_edge_cases() -> None:
    combined = [*EN_CORPUS, *TR_CORPUS]
    assert _has_match(combined, "https://"), "corpus needs a URL sample"
    assert _has_match(combined, "`"), "corpus needs an inline code span"
    assert _has_match(combined, "\\cite{"), "corpus needs a LaTeX citation"
    assert any(ch.isdigit() for sample in combined for ch in sample.text)
    assert any(
        ch in "çğıöşüÇĞİÖŞÜ" for sample in TR_CORPUS for ch in sample.text
    ), "Turkish corpus needs Turkish-specific letters"


def test_checks_are_not_vacuous() -> None:
    sample = EN_CORPUS[0]
    broken = sample.text.replace("\n\n", " ")
    checks = {check.name: check for check in run_checks(sample, broken)}
    assert not checks["structure_ok"].passed
    unchanged = {check.name: check for check in run_checks(sample, sample.text)}
    assert not unchanged["changed"].passed
