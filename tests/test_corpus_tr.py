"""Large-scale scan of the Turkish rule table against academic prose.

``scan`` rewrites every corpus sample and inspects the result for structural
damage, punctuation/word artifacts, broken grammar, protected-span changes and
non-idempotency. Every finding is attributed to the rule that most plausibly
produced it, so the report can be grouped by rule.

The heuristics are deliberately conservative: a false alarm costs more than a
miss here, because the point is to remove rules that demonstrably damage text.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass
from functools import lru_cache

from corpus_tr_academic import SAMPLE_META, SAMPLES

from textscope import rules_tr
from textscope.protected import verify_protected
from textscope.rewrite import rewrite_text

DAMAGING = (
    "grammar_broken",
    "artifact",
    "structure_changed",
    "protected_changed",
    "idempotent_violation",
)
INFORMATIONAL = ("meaning_shift", "not_changed")


@dataclass(frozen=True)
class Issue:
    sample: int
    rule: str
    category: str
    before: str
    after: str
    detail: str = ""


@dataclass(frozen=True)
class _Change:
    orig_start: int
    out_start: int
    before: str
    after: str
    rule: str


_TR_WORD = r"A-Za-zÇĞİÖŞÜçğıöşü"
_TOKEN = re.compile(rf"[{_TR_WORD}]+")
_NONSPACE = re.compile(r"\S+")


_ABBREV_TAIL = re.compile(
    r"\b(?:vd|vb|bkz|ss|vs|no|ör|yy|dr|prof|doç|mö|ms|[A-ZÇĞİÖŞÜ]|\d)\.[\"')\]]*$",
    re.IGNORECASE,
)


def _sentences(text: str) -> list[str]:
    """Split into sentences without breaking after Turkish abbreviations."""
    parts = re.split(r"(?<=[.!?])\s+", text)
    merged: list[str] = []
    for part in parts:
        if merged and _ABBREV_TAIL.search(merged[-1].strip()):
            merged[-1] = merged[-1] + " " + part
        else:
            merged.append(part)
    return [s for s in merged if s.strip()]


def _sentence_at(text: str, pos: int) -> str:
    while pos < len(text) and text[pos].isspace():
        pos += 1
    start = text.rfind(".", 0, pos) + 1
    end = text.find(".", pos)
    end = len(text) if end == -1 else end + 1
    return text[start:end].strip()


def _words(text: str) -> list[str]:
    return _TOKEN.findall(text)


def _phrase_hint(pattern: str) -> str:
    return pattern.replace(r"\b", "").strip()


# ---------------------------------------------------------------- attribution

_WORD_KEYS = {k.lower() for k in rules_tr.WORD_SWAPS_TR}
_EXTRA_KEYS = {k.lower() for k in rules_tr.EXTRA_WORD_SWAPS_TR}


def _phrase_candidates(text: str) -> list[tuple[int, int, str]]:
    out: list[tuple[int, int, str]] = []
    for pattern, _ in rules_tr.PHRASE_SWAPS_TR:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            out.append((m.start(), m.end(), _phrase_hint(pattern)))
    out.sort(key=lambda item: (item[0], -(item[1] - item[0])))
    return out


_FORMAL_VERB = re.compile(
    r"(?:mektedir|maktadır|mıştır|miştir|muştur|müştür|ecektir|acaktır|"
    r"malıdır|melidir|mekte|makta|mış|miş|muş|müş)$"
)


def _attribute(before: str, after: str, orig_start: int,
               phrases: list[tuple[int, int, str]]) -> str:
    before_low = before.lower()
    for token in _words(before_low):
        if token in _WORD_KEYS:
            return token
    for token in _words(before_low):
        if token in _EXTRA_KEYS:
            return f"extra:{token}"
    for start, end, hint in phrases:
        if start <= orig_start < end:
            return hint
    for token in _words(before_low):
        if _FORMAL_VERB.search(token):
            return "turkish_forms"
    return "unknown"


def _diff_changes(src: str, out: str) -> list[_Change]:
    a = [(m.group(0), m.start()) for m in _NONSPACE.finditer(src)]
    b = [(m.group(0), m.start()) for m in _NONSPACE.finditer(out)]
    sm = difflib.SequenceMatcher(a=[t for t, _ in a], b=[t for t, _ in b],
                                 autojunk=False)
    phrases = _phrase_candidates(src)
    changes: list[_Change] = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        before = src[a[i1][1]: a[i2 - 1][1] + len(a[i2 - 1][0])] if i2 > i1 else ""
        after = out[b[j1][1]: b[j2 - 1][1] + len(b[j2 - 1][0])] if j2 > j1 else ""
        orig_start = a[i1][1] if i1 < len(a) else len(src)
        out_start = b[j1][1] if j1 < len(b) else len(out)
        rule = _attribute(before, after, orig_start, phrases)
        changes.append(_Change(orig_start, out_start, before, after, rule))
    return changes


def _rule_for_pos(changes: list[_Change], pos: int) -> str:
    best: _Change | None = None
    for change in changes:
        if change.out_start <= pos and (best is None or change.out_start >= best.out_start):
            best = change
    return best.rule if best else "unknown"


def _rule_for_span(changes: list[_Change], start: int, end: int) -> str:
    for change in changes:
        if change.out_start < end and change.out_start + len(change.after) > start:
            return change.rule
    return _rule_for_pos(changes, start)


# ------------------------------------------------------------------ artifacts

_DOUBLE_SPACE = re.compile(r"[^\S\n]{2,}")
_SPACE_BEFORE_PUNCT = re.compile(r"[^\s(\[][ \t]+[.,;:!?]")
_DOUBLED_WORD = re.compile(rf"\b([{_TR_WORD}]+)\s+\1\b", re.IGNORECASE)
_DOUBLED_PUNCT = re.compile(r"[,;:]{2,}|(?<!\.)\.\.(?!\.)")
_DANGLING = re.compile(
    r"\b(ve|veya|ama|ancak|çünkü|ile|için|gibi|kadar|olan|bir|bu|hem|ya|da|de|ki)"
    r"[.!?]\s*$",
    re.IGNORECASE,
)


def _glued_pair_set(text: str) -> set[str]:
    tokens = [t.lower() for t in _words(text)]
    return {tokens[i] + tokens[i + 1] for i in range(len(tokens) - 1)}


def _artifact_issues(i: int, src: str, out: str,
                     changes: list[_Change]) -> list[Issue]:
    found: list[Issue] = []
    src_tokens = {t.lower() for t in _words(src)}

    def add(match: re.Match, detail: str) -> None:
        found.append(Issue(
            sample=i,
            rule=_rule_for_span(changes, match.start(), match.end()),
            category="artifact",
            before=_sentence_at(src, changes[0].orig_start if changes else 0),
            after=_sentence_at(out, match.start()),
            detail=detail,
        ))

    for m in _DOUBLE_SPACE.finditer(out):
        add(m, "double space")
    for m in _SPACE_BEFORE_PUNCT.finditer(out):
        add(m, "space before punctuation")
    for m in _DOUBLED_WORD.finditer(out):
        add(m, f"doubled word {m.group(1)!r}")
    for m in _DOUBLED_PUNCT.finditer(out):
        add(m, "doubled punctuation")

    pairs = _glued_pair_set(src)
    for m in _TOKEN.finditer(out):
        token = m.group(0)
        if token.lower() in pairs and token.lower() not in src_tokens:
            found.append(Issue(i, _rule_for_pos(changes, m.start()), "artifact",
                               _sentence_at(src, changes[0].orig_start if changes else 0),
                               _sentence_at(out, m.start()),
                               f"glued words {token!r}"))

    for index, sentence in enumerate(_sentences(out)):
        if index and sentence[:1].islower():
            prev = _sentences(out)[index - 1]
            if not _ABBREV_TAIL.search(prev.strip()):
                found.append(Issue(i, _rule_for_pos(changes, out.find(sentence)),
                                   "artifact",
                                   _sentence_at(src, changes[0].orig_start if changes else 0),
                                   sentence, "sentence starts lowercase"))
        if _DANGLING.search(sentence):
            found.append(Issue(i, "split_long_sentences", "artifact",
                               _sentence_at(src, changes[0].orig_start if changes else 0),
                               sentence, "dangling conjunction"))
        if sentence.rstrip().endswith((",", ";")):
            found.append(Issue(i, "split_long_sentences", "artifact",
                               _sentence_at(src, changes[0].orig_start if changes else 0),
                               sentence, "sentence ends with a comma"))
    return found


# -------------------------------------------------------------------- grammar

_BAD_LIGHT_NOUN = (
    r"(?:inceleme|sunum|ölçme|değerlendirme|gözlem|uygulama|saptama|anlatma|"
    r"açıklama|sınıflama|karşılaştırma|tanımlama|betimleme|çözümleme|kurgulama)"
)
_LIGHT_VERB = (
    r"(?:edilmesi|edilmesini|edilmesine|edilmesinde|edilerek|edilmiştir|"
    r"edilmektedir|edilecektir|edilmelidir|etmektedir|etmiştir|etmek|etmeyi|"
    r"eden|edilen)"
)
_BROKEN_LIGHT_NOUN = re.compile(rf"\b{_BAD_LIGHT_NOUN}\s+{_LIGHT_VERB}\b", re.IGNORECASE)
_BROKEN_VERB_LIGHT = re.compile(
    rf"\b[{_TR_WORD}]+(?:ıyor|iyor|uyor|üyor|d[ıi]|m[ıi]ş)\s+{_LIGHT_VERB}\b",
    re.IGNORECASE,
)
_DATIVE_BEFORE_HAKKINDA = re.compile(
    r"\b[a-zçğıöşü]{3,}(?:[ae]|ya|ye)\s+hakkında\b"
)
_IMPOSSIBLE_SUFFIX = re.compile(
    rf"\b[{_TR_WORD}]+(?:mekte|makta)(?:dır|dir)(?:mek|mak)"
    rf"|[{_TR_WORD}]+(?:dır|dir|dur|dür)(?:dır|dir|dur|dür)\b",
    re.IGNORECASE,
)
_VERB_SUFFIX = re.compile(
    r"(?:yor(?:um|sun|uz|lar)?|[dt][ıi]k?|m[ıi]ş|m[ıi]şt[ıi]r|acak|ecek|"
    r"malı|meli|mekte|makta|m[ae]kt[ıi]r|d[ıi]r|mek|mak|s[ıi]n|s[ıi]n[ıi]z|[ıi]z|"
    r"[ae]bilir|y[ıi]m)$"
)
_NOMINAL_PREDICATE = {"var", "yok", "değil", "değildir", "gerekli", "gerek",
                      "önemli", "olası", "mümkün", "sınırlı", "güç", "yeterli"}


def _verbless(sentence: str) -> bool:
    words = [w.lower() for w in _words(sentence)]
    if len(words) < 6:
        return False
    if any(w in _NOMINAL_PREDICATE for w in words):
        return False
    # A nominal predicate ("... ile bağlantılı", "... için önemli") is a
    # complete Turkish sentence; do not demand a finite verb there.
    if re.search(r"(?:l[ıiuü]|s[ıiuü]z|ki|d[ıiuü]r)$", words[-1]):
        return False
    return not any(_VERB_SUFFIX.search(w) for w in words)


def _grammar_issues(i: int, src: str, out: str,
                    changes: list[_Change]) -> list[Issue]:
    found: list[Issue] = []
    for pattern, detail in (
        (_BROKEN_LIGHT_NOUN, "light-verb construction broken"),
        (_BROKEN_VERB_LIGHT, "verb followed by a light verb"),
        (_IMPOSSIBLE_SUFFIX, "impossible suffix combination"),
        (_DATIVE_BEFORE_HAKKINDA, "case suffix before a nominative postposition"),
    ):
        for m in pattern.finditer(out):
            found.append(Issue(i, _rule_for_span(changes, m.start(), m.end()), "grammar_broken",
                               _sentence_at(src, changes[0].orig_start if changes else 0),
                               _sentence_at(out, m.start()), detail))
    for sentence in _sentences(out):
        low = sentence.lower()
        if "hem" in low and "ayrıca" in low and "hem de" not in low:
            found.append(Issue(i, "hem de", "grammar_broken",
                               _sentence_at(src, changes[0].orig_start if changes else 0),
                               sentence, "hem ... hem de construction broken"))
        if _verbless(sentence):
            found.append(Issue(i, _rule_for_pos(changes, out.find(sentence)),
                               "grammar_broken",
                               _sentence_at(src, changes[0].orig_start if changes else 0),
                               sentence, "sentence has no finite verb"))
    return found


# ------------------------------------------------------------ meaning (info)

_NEGATIONS = ("değil", "yok", "yoktur", "olmaz", "olmamış", "yapılmamış",
              "edilmemiş", "kalmamış", "görülmemiş", "değildir")
_HEDGES = ("anlamlı", "istatistiksel", "nedensel", "genellenebilir",
           "güvenilir", "geçerli", "yaklaşık")
# Adverbials that carry a timeframe or an enumeration order. Removing one is a
# content deletion, not a stylistic simplification.
_CONTENT_MARKERS = (
    "son yıllarda", "son dönemde", "son zamanlarda", "yakın zamanda",
    "şimdilerde", "kısa vadede", "uzun vadede", "ilk bakışta",
    "başlangıçta", "bu sırada", "bu arada", "bu esnada", "aynı zamanda",
    "öncelikle", "ilk olarak", "ikinci olarak", "üçüncü olarak", "son olarak",
)
# Terms of art where the table used a near-synonym that changes the technical
# claim (sustainability is not permanence, a difference is not a distinction).
_TERM_DRIFT = (
    "sürdürülebilir", "farklılık", "değerlendirme", "değerlendirilmesi",
    "değerlendirilmesinde", "değerlendirildiğinde", "evren", "kapasite",
    "boyut", "vizyon", "misyon", "analiz", "süreç", "yaygın",
    "doğrultusunda",
)


def _meaning_issues(i: int, src: str, out: str,
                    changes: list[_Change]) -> list[Issue]:
    """Flag content that was dropped or replaced by a near-synonym.

    Attribution goes through the diff, so the excerpt shows the sentence the
    damage actually happened in rather than the whole sample.
    """
    found: list[Issue] = []
    src_low = src.lower()
    out_low = out.lower()

    def add(rule: str, change: _Change, detail: str) -> None:
        found.append(Issue(
            i, rule, "meaning_shift",
            _sentence_at(src, change.orig_start),
            _sentence_at(out, change.out_start),
            detail,
        ))

    for change in changes:
        before_low = change.before.lower()
        after_low = change.after.lower()
        for marker in _CONTENT_MARKERS:
            if marker in before_low and marker not in after_low:
                add(marker, change, "content-bearing adverbial dropped")
        for term in _TERM_DRIFT:
            if term in before_low and term not in after_low:
                add(term, change, "term of art replaced with a near-synonym")
        for hedge in _HEDGES:
            if hedge in before_low and hedge not in after_low:
                add(hedge, change, f"statistical term {hedge!r} removed")

    for negation in _NEGATIONS:
        if src_low.count(negation) > out_low.count(negation):
            found.append(Issue(i, "negation", "meaning_shift", negation,
                               "count decreased", "negation dropped"))
    return found


# --------------------------------------------------------------------- scan


def scan(samples: list[str], seed: int = 0, check_idempotency: bool = True) -> list[Issue]:
    issues: list[Issue] = []
    for i, src in enumerate(samples):
        out = rewrite_text(src, seed=seed)
        changes = _diff_changes(src, out)

        ok, errors = verify_protected(src, out)
        if not ok:
            issues.append(Issue(i, "protected", "protected_changed", src[:80],
                                out[:80], "; ".join(errors)))

        if src.count("\n") != out.count("\n"):
            issues.append(Issue(i, "rewrite_document", "structure_changed",
                                f"{src.count(chr(10))} newlines",
                                f"{out.count(chr(10))} newlines"))
        src_paras = [p for p in re.split(r"\n\s*\n", src) if p.strip()]
        out_paras = [p for p in re.split(r"\n\s*\n", out) if p.strip()]
        if len(src_paras) != len(out_paras):
            issues.append(Issue(i, "rewrite_document", "structure_changed",
                                f"{len(src_paras)} paragraphs",
                                f"{len(out_paras)} paragraphs"))

        issues.extend(_artifact_issues(i, src, out, changes))
        issues.extend(_grammar_issues(i, src, out, changes))
        issues.extend(_meaning_issues(i, src, out, changes))

        if out.strip() == src.strip():
            issues.append(Issue(i, "none", "not_changed", src[:80], out[:80]))

        if check_idempotency:
            again = rewrite_text(out, seed=seed)
            if again != out:
                pos = next((k for k, (a, b) in enumerate(zip(again, out)) if a != b),
                           min(len(again), len(out)))
                issues.append(Issue(i, "second_pass", "idempotent_violation",
                                    out[max(0, pos - 40):pos + 60],
                                    again[max(0, pos - 40):pos + 60],
                                    "rewriting twice changes the text"))

    # One issue per (sample, category, rule): the count then means "this rule
    # damaged N samples", not "N punctuation marks".
    unique: dict[tuple[int, str, str], Issue] = {}
    for issue in issues:
        unique.setdefault((issue.sample, issue.category, issue.rule), issue)
    return list(unique.values())


def group_issues(issues: list[Issue], category: str | None = None
                 ) -> dict[str, int]:
    counts: dict[str, int] = {}
    for issue in issues:
        if category and issue.category != category:
            continue
        key = f"{issue.rule}" if not issue.detail else f"{issue.rule} [{issue.detail}]"
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: -kv[1]))


def category_counts(issues: list[Issue]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for issue in issues:
        counts[issue.category] = counts.get(issue.category, 0) + 1
    return counts


@lru_cache(maxsize=1)
def cached_scan() -> tuple[Issue, ...]:
    return tuple(scan(SAMPLES))


# --------------------------------------------------------------------- tests


def test_corpus_size_and_coverage() -> None:
    assert len(SAMPLES) >= 250
    assert len(SAMPLE_META) == len(SAMPLES)
    registers = {meta["register"] for meta in SAMPLE_META}
    assert len(registers) >= 12, registers
    domains = {meta["domain"] for meta in SAMPLE_META}
    assert len(domains) >= 10, domains
    assert sum(1 for meta in SAMPLE_META if meta["has_protected"]) >= 40


def test_every_sample_is_three_to_six_sentences() -> None:
    for index, sample in enumerate(SAMPLES):
        count = len(_sentences(sample))
        assert 3 <= count <= 6, (index, count, sample)


def test_samples_are_grammatical_by_construction() -> None:
    # The corpus is template-built; a stray slot outside a domain dict would
    # survive as "{topic}" and must be treated as a corpus bug.
    slot = re.compile(r"\{(?:topic|tgen|tloc|tdat|field|pop|pgen|method|mgen|"
                      r"sloc|sdat|unit|unit_pl)\}")
    for index, sample in enumerate(SAMPLES):
        assert not slot.search(sample), (index, sample)
        assert "  " not in sample, (index, sample)


def test_corpus_contains_protected_constructs() -> None:
    joined = " ".join(SAMPLES)
    assert "%" in joined
    assert "2019" in joined
    assert "(Yılmaz, 2019" in joined
    assert "\\cite{" in joined
    assert "https://" in joined
    assert "vd." in joined
    assert "vb." in joined
    assert "bkz." in joined
    assert "ss." in joined


def test_scan_has_no_damaging_issues() -> None:
    issues = list(cached_scan())
    counts = category_counts(issues)
    damaging = {name: counts.get(name, 0) for name in DAMAGING}
    detail = "\n".join(
        f"{issue.category} | {issue.rule} | sample {issue.sample}: {issue.detail}"
        for issue in issues
        if issue.category in DAMAGING
    )
    assert all(count == 0 for count in damaging.values()), f"{damaging}\n{detail}"
