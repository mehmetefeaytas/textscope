from __future__ import annotations

import random
import re

from .protected import split_protected
from .rules_en import (
    CONTRACTIONS_EN,
    EXTRA_PHRASE_SWAPS_EN,
    EXTRA_WORD_SWAPS_EN,
    LEADING_TRANSITIONS_EN,
    PHRASE_SWAPS_EN,
    WORD_SWAPS_EN,
    WORD_VARIANTS_EN,
)
from .rules_tr import (
    CONTRACTIONS_TR,
    EXTRA_WORD_SWAPS_TR,
    LEADING_TRANSITIONS_TR,
    PHRASE_SWAPS_TR,
    TR_STOPWORDS,
    WORD_SWAPS_TR,
    WORD_VARIANTS_TR,
)

_TR_CHARS = frozenset("çğıöşüÇĞİÖŞÜ")



def detect_language(text: str) -> str:
    """Detect Turkish vs English with no external dependency.

    Turkish is recognised by its special letters *and* by a ratio of common
    function words, so ASCII-only Turkish ("calisma") is still detected.
    """
    if not text.strip():
        return "en"
    tr_char_hits = sum(1 for ch in text if ch in _TR_CHARS)
    tokens = re.findall(r"[^\W\d_]+", text.lower())
    if not tokens:
        return "en"
    tr_word_hits = sum(1 for t in tokens if t in TR_STOPWORDS)
    ratio = tr_word_hits / len(tokens)
    if tr_char_hits >= 2 and ratio >= 0.03:
        return "tr"
    if ratio >= 0.08:
        return "tr"
    if tr_char_hits >= 4:
        return "tr"
    return "en"


def _rules(lang: str):
    if lang == "tr":
        return (WORD_SWAPS_TR, PHRASE_SWAPS_TR, LEADING_TRANSITIONS_TR, CONTRACTIONS_TR)
    return (WORD_SWAPS_EN, PHRASE_SWAPS_EN, LEADING_TRANSITIONS_EN, CONTRACTIONS_EN)


def _upper_first(text: str, lang: str = "en") -> str:
    """Uppercase the first letter, honouring Turkish i/ı."""
    if not text:
        return text
    first = text[0]
    if lang == "tr" and first == "i":
        first = "İ"
    elif lang == "tr" and first == "ı":
        first = "I"
    else:
        first = first.upper()
    return first + text[1:]


def _preserve_case(original: str, replacement: str, lang: str = "en") -> str:
    if original and replacement and original[0].isupper():
        return _upper_first(replacement, lang)
    return replacement


def _apply_word_swaps(text: str, swaps: dict, lang: str = "en") -> str:
    if not swaps:
        return text
    pattern = r"\b(" + "|".join(re.escape(k) for k in sorted(swaps, key=len, reverse=True)) + r")\b"
    def repl(m):
        w = m.group(0)
        low = w.lower()
        if low in swaps:
            return _preserve_case(w, swaps[low], lang)
        return w
    return re.sub(pattern, repl, text, flags=re.IGNORECASE)


def _apply_phrase_swaps(text: str, swaps: list, lang: str = "en") -> str:
    for pat, rep in swaps:
        def repl(m, rep=rep):
            return _preserve_case(m.group(0), rep, lang)
        text = re.sub(pat, repl, text, flags=re.IGNORECASE)
    return text


def _remove_leading_transitions(text: str, transitions: list, lang: str = "en") -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    out = []
    for s in sentences:
        s2 = s
        for tr in transitions:
            m = re.match(r"(\s*)" + re.escape(tr) + r"\b\s*,?\s*", s2, flags=re.IGNORECASE)
            if m:
                lead = m.group(1)
                rest = s2[m.end():]
                if rest.strip():
                    s2 = lead + rest
                    stripped = s2.lstrip()
                    if stripped and stripped[0].islower():
                        idx = len(s2) - len(stripped)
                        s2 = s2[:idx] + _upper_first(stripped, lang)
                break
        out.append(s2)
    return " ".join(out)


def _apply_contractions(text: str, contractions: list, lang: str = "en") -> str:
    def repl(m, rep):
        return _preserve_case(m.group(0), rep, lang)

    for pat, rep in contractions:
        text = re.sub(pat, lambda m, r=rep: repl(m, r), text, flags=re.IGNORECASE)
    return text


# ---------- Turkish verb forms ----------
#
# Turkish academic prose is dominated by "-mektedir" and "-mıştır". Swapping
# whole word lists is not enough because the suffix carries the tense. These
# rules convert the suffix generically while keeping it one word -> one word,
# so --strict word counts still hold.

_TR_VOWELS = "aeıioöuü"
_TR_HARMONY = {"a": "ı", "ı": "ı", "e": "i", "i": "i",
               "o": "u", "u": "u", "ö": "ü", "ü": "ü"}
_TR_VOICELESS = frozenset("çfhkpsşt")
_TR_PROGRESSIVE_STEMS = {"et": "ed", "git": "gid", "tat": "tad"}
_TR_COPULA_EXCEPTIONS = frozenset({"müdür", "kudur", "hüdür"})
_TR_WORD_CHARS = "A-Za-zÇĞİÖŞÜçğıöşü"

_TR_PROGRESSIVE_RE = re.compile(
    rf"\b([{_TR_WORD_CHARS}]{{2,}}?)(mekte|makta)(dır|dir)(ler|lar)?\b")
_TR_PAST_RE = re.compile(
    rf"\b([{_TR_WORD_CHARS}]{{2,}}?)(mış|miş|muş|müş)(lar|ler)?(dır|dir|dur|dür|tır|tir|tur|tür)\b")
_TR_FUTURE_RE = re.compile(
    rf"\b([{_TR_WORD_CHARS}]{{2,}}?)(ecek|acak)(lar|ler)?(tır|tir|tur|tür)\b")
_TR_NECESSITY_RE = re.compile(
    rf"\b([{_TR_WORD_CHARS}]{{2,}}?)(malı|meli)(dır|dir)\b")
_TR_COPULA_RE = re.compile(
    rf"\b([{_TR_WORD_CHARS}]{{3,}}?)(dır|dir|dur|dür)\b")


def _last_vowel(word: str) -> str:
    for ch in reversed(word):
        if ch in _TR_VOWELS:
            return ch
    return "ı"


def _progressive(stem: str) -> str:
    """gel- -> geliyor, yapıl- -> yapılıyor, oku- -> okuyor, et- -> ediyor."""
    if stem[-1] in _TR_VOWELS:
        base = stem[:-1]
        vowel = _TR_HARMONY[stem[-1]]
    else:
        base = _TR_PROGRESSIVE_STEMS.get(stem, stem)
        vowel = _TR_HARMONY[_last_vowel(stem)]
    return base + vowel + "yor"


def _simple_past(stem: str) -> str:
    """yapıl- -> yapıldı, et- -> etti, oku- -> okudu."""
    vowel = _TR_HARMONY[_last_vowel(stem)]
    consonant = "t" if stem[-1] in _TR_VOICELESS else "d"
    return stem + consonant + vowel


def _apply_turkish_forms(text: str, aggressive: bool = False) -> str:
    """Soften formal Turkish verb endings without changing the word count."""
    def restore(original: str, result: str) -> str:
        return _upper_first(result, "tr") if original[:1].isupper() else result

    def progressive(m):
        result = _progressive(m.group(1).lower())
        if m.group(4):
            result += "lar"
        return restore(m.group(0), result)

    def past(m):
        result = _simple_past(m.group(1).lower())
        if m.group(3):
            result += "lar"
        return restore(m.group(0), result)

    def future(m):
        result = m.group(1).lower() + m.group(2)
        if m.group(3):
            result += "lar"
        return restore(m.group(0), result)

    def necessity(m):
        return restore(m.group(0), m.group(1).lower() + m.group(2))

    def copula(m):
        stem = m.group(1)
        if len(stem) < 3 or stem.lower() in _TR_COPULA_EXCEPTIONS:
            return m.group(0)
        return restore(m.group(0), stem)

    text = _TR_PROGRESSIVE_RE.sub(progressive, text)
    text = _TR_PAST_RE.sub(past, text)
    text = _TR_FUTURE_RE.sub(future, text)
    text = _TR_NECESSITY_RE.sub(necessity, text)
    if aggressive:
        text = _TR_COPULA_RE.sub(copula, text)
    return text


_DUP_WORD = re.compile(r"\b(\w+)([ \t]+)\1\b", re.IGNORECASE)

# Past-tense swaps can create impossible auxiliaries ("have showed"). Repair the
# handful of irregular verbs that the word table touches.
_EN_AUX_FIXES = [
    (r"\b(have|has|had|having|was|were|is|are|be|been|being)\s+showed\b", r"\1 shown"),
    (r"\b(have|has|had|having)\s+grew\b", r"\1 grown"),
    (r"\b(have|has|had|having)\s+ran\b", r"\1 run"),
    (r"\b(have|has|had|having)\s+went\b", r"\1 gone"),
    (r"\b(have|has|had|having)\s+dug\b", r"\1 dug"),
]


def _fix_english_grammar(text: str) -> str:
    for pattern, replacement in _EN_AUX_FIXES:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return _fix_articles(text)


_ARTICLE_RE = re.compile(r"\b(a|an|A|An)\s+([A-Za-z][A-Za-z'-]*)")
# words starting with a vowel letter but a consonant sound, and vice versa
_A_BEFORE_VOWEL = ("uni", "use", "usu", "uti", "ure", "uro", "eu", "one",
                   "once", "ubiq", "unanim", "ufo")
_AN_BEFORE_CONSONANT = ("hour", "honest", "honor", "honour", "heir")


def _fix_articles(text: str) -> str:
    """Repair "a important" -> "an important" after adjective swaps."""

    def repl(m: re.Match) -> str:
        article, word = m.group(1), m.group(2)
        low = word.lower()
        needs_an = low[0] in "aeiou" and not low.startswith(_A_BEFORE_VOWEL)
        needs_an = needs_an or low.startswith(_AN_BEFORE_CONSONANT)
        if needs_an and article.lower() == "a":
            article = "An" if article[0].isupper() else "an"
        elif not needs_an and article.lower() == "an":
            article = "A" if article[0].isupper() else "a"
        return f"{article} {word}"

    return _ARTICLE_RE.sub(repl, text)


_DUP_STARTERS = frozenset({"also", "besides", "however", "therefore", "thus",
                           "still", "so", "plus"})


def _dedupe_sentence_starters(text: str, lang: str = "en") -> str:
    """Avoid "Also, ... Also, ..." runs created by connector swaps."""
    sentences = _SENT_SPLIT.split(text)
    out: list[str] = []
    previous: str | None = None
    for sentence in sentences:
        m = re.match(r"(\s*)([A-Za-zÇĞİÖŞÜçğıöşü]+)(,\s+)", sentence)
        word = m.group(2).lower() if m else None
        if m and word == previous and word in _DUP_STARTERS:
            rest = sentence[m.end():]
            if rest.strip():
                sentence = m.group(1) + _upper_first(rest, lang)
        out.append(sentence)
        previous = word
    return " ".join(out)


def _collapse_duplicate_words(text: str) -> str:
    """Kill "Bu bu çalışmada" / "the the" artifacts left by phrase swaps."""
    previous = None
    while previous != text:
        previous = text
        text = _DUP_WORD.sub(lambda m: m.group(1), text)
    return text


_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")
_SPLIT_CONJUNCTIONS = (
    " and ", " but ", " because ", " although ", " while ",
    " ve ", " ama ", " çünkü ", " ancak ",
)


_CLAUSE_STARTERS_EN = frozenset({
    "it", "this", "that", "these", "those", "they", "we", "you", "he", "she",
    "there", "its", "their", "our", "his", "her", "i", "one",
    "however", "but", "so", "yet", "then", "which", "while", "whereas",
    "although", "though", "because", "since", "and",
})

_CLAUSE_STARTERS_TR = frozenset({
    "bu", "bunlar", "bunun", "burada", "o", "onlar", "biz", "siz",
    "ancak", "fakat", "ama", "çünkü", "dolayısıyla", "böylece", "sonuçta",
    "yani", "üstelik", "ayrıca", "buna", "bununla", "öte", "diğer",
})

# A sentence must not be cut right after one of these; the result would be a
# dangling fragment such as "the study looked at a full."
_DANGLING_TAIL = frozenset({
    "a", "an", "the", "of", "in", "on", "at", "for", "to", "with", "by",
    "from", "as", "and", "or", "but", "that", "which", "than", "into",
    "over", "under", "between", "bir", "bu", "ve", "ile", "için", "olan",
    "gibi", "kadar", "ya", "veya", "ama", "hem",
})


_CLAUSE_SUBJECTS_EN = frozenset({
    "it", "this", "that", "these", "those", "they", "we", "you", "he", "she",
    "i", "there", "one", "who", "which", "what",
    "the", "a", "an", "its", "their", "our", "his", "her", "my", "your",
    "can", "will", "would", "should", "could", "may", "might", "must",
    "is", "are", "was", "were", "has", "have", "had", "do", "does", "did",
})

_CLAUSE_SUBJECTS_TR = frozenset({
    "bu", "bunlar", "bunun", "bununla", "o", "onlar", "biz", "siz", "ben",
    "ancak", "fakat", "ama", "çünkü", "dolayısıyla", "böylece", "sonuçta",
    "yani", "üstelik", "ayrıca", "öte", "diğer", "buna", "her", "tüm",
})


def _looks_like_clause_start(right: str, lang: str) -> bool:
    """True when ``right`` plausibly opens its own clause.

    Guards the conjunction split: "a comprehensive and multifaceted approach"
    must not become "a full. Complex way", because "complex" is an adjective,
    not a subject.
    """
    first = right.split(maxsplit=1)
    if not first:
        return False
    word = first[0].strip(",;:").lower()
    subjects = _CLAUSE_SUBJECTS_TR if lang == "tr" else _CLAUSE_SUBJECTS_EN
    return word in subjects


def _clause_starter_ok(right: str, lang: str) -> bool:
    """True when ``right`` opens a new clause rather than continuing a list.

    This is what stops the splitter from cutting "economic, environmental, and
    social dimensions" into "... economic. Environmental and social dimensions".
    After a list comma comes an ordinary noun or adjective, not a clause opener.
    """
    first = right.split(maxsplit=1)
    if not first:
        return False
    word = first[0].strip(",;:").lower()
    starters = _CLAUSE_STARTERS_TR if lang == "tr" else _CLAUSE_STARTERS_EN
    return word in starters


def _split_sentence(sentence: str, min_part: int, lang: str = "en") -> list[str] | None:
    """Split at a conjunction or comma, but only into two real clauses.

    Both halves must carry at least ``min_part`` words, otherwise we return None
    and keep the sentence intact. This is what stops the tool from turning
    "In today's evolving landscape, AI matters." into a 5-word fragment.
    """
    low = sentence.lower()
    cuts: list[tuple[int, int]] = []
    for conj in _SPLIT_CONJUNCTIONS:
        start = 0
        while (idx := low.find(conj, start)) != -1:
            cuts.append((idx, idx + len(conj)))
            start = idx + 1
    start = 0
    while (idx := sentence.find(",", start)) != -1:
        cuts.append((idx, idx + 1))
        start = idx + 1

    best: tuple[int, str, str] | None = None
    for cut_start, cut_end in cuts:
        left = sentence[:cut_start].strip()
        right = sentence[cut_end:].strip()
        if len(left.split()) < min_part or len(right.split()) < min_part:
            continue
        if left.split()[-1].strip(",;:").lower() in _DANGLING_TAIL:
            continue
        is_conjunction_cut = sentence[cut_start:cut_end].strip().lower() in {
            conj.strip() for conj in _SPLIT_CONJUNCTIONS
        }
        if not _looks_like_clause_start(right, lang):
            continue
        # commas are only trusted when a new clause clearly starts after them
        if not is_conjunction_cut and not _clause_starter_ok(right, lang):
            continue
        balance = abs(len(left.split()) - len(right.split()))
        if best is None or balance < best[0]:
            best = (balance, left, right)
    if best is None:
        return None

    _, left, right = best
    left = left.rstrip(",;:").rstrip() + "."
    right = _upper_first(right, lang)
    if not right.endswith((".", "!", "?")):
        right = right.rstrip(",;:").rstrip() + "."
    return [left, right]


def _split_long_sentences(text: str, min_part: int = 6, lang: str = "en") -> str:
    out: list[str] = []
    for sentence in _SENT_SPLIT.split(text):
        if len(sentence.split()) < 2 * min_part:
            out.append(sentence)
            continue
        parts = _split_sentence(sentence, min_part, lang)
        out.extend(parts if parts else [sentence])
    return " ".join(out)


def _break_chains(swaps: dict[str, str]) -> dict[str, str]:
    """Drop any swap whose output is itself a key.

    Otherwise a second pass rewrites the result again and the tool is not
    idempotent: ``framework -> structure -> shape`` changed the text every time
    it ran. Dropping the first hop keeps the more conservative word, which is
    also the safer choice for meaning.
    """
    keys = set(swaps)
    return {key: value for key, value in swaps.items() if value not in keys}


def _pick_variants(swaps: dict, rng: random.Random, lang: str) -> dict:
    table = WORD_VARIANTS_TR if lang == "tr" else WORD_VARIANTS_EN
    return {k: (rng.choice(table[k]) if k in table else v) for k, v in swaps.items()}


def rewrite_free(text: str, strict: bool = False, seed: int = 0, lang: str = "auto",
                 aggressive: bool = False) -> str:
    if not text.strip():
        return text
    if lang == "auto":
        lang = detect_language(text)
    swaps, phrases, transitions, contractions = _rules(lang)
    original_text = text
    rng = random.Random(seed)
    swaps = _pick_variants(swaps, rng, lang)

    if aggressive:
        extra_swaps = EXTRA_WORD_SWAPS_TR if lang == "tr" else EXTRA_WORD_SWAPS_EN
        swaps = {**swaps, **extra_swaps}
        if lang != "tr":
            phrases = list(phrases) + EXTRA_PHRASE_SWAPS_EN

    # Guarantee idempotency regardless of what the data tables contain.
    swaps = _break_chains(swaps)

    if strict:
        # Only 1-word -> 1-word swaps are safe; multi-word replacements would
        # shift the count, so they are filtered out for --strict.
        safe_swaps = {k: v for k, v in swaps.items() if len(k.split()) == len(v.split())}
        text = _apply_word_swaps(text, safe_swaps, lang)
        if lang == "tr":
            text = _apply_turkish_forms(text, aggressive=aggressive)
        else:
            text = _fix_english_grammar(text)
        if len(text.split()) != len(original_text.split()):
            text = original_text
        return _collapse_duplicate_words(text)

    # --seed also picks the split threshold and whether contractions apply.
    min_part = 6 if aggressive else rng.choice([6, 7, 8])
    use_contractions = aggressive or rng.random() < 0.8

    text = _apply_phrase_swaps(text, phrases, lang)
    text = _apply_word_swaps(text, swaps, lang)
    if lang == "tr":
        text = _apply_turkish_forms(text, aggressive=aggressive)
    else:
        text = _fix_english_grammar(text)
    text = _remove_leading_transitions(text, transitions, lang)
    if use_contractions:
        text = _apply_contractions(text, contractions, lang)
    if lang != "tr":
        text = _dedupe_sentence_starters(text, lang)
    text = _split_long_sentences(text, min_part=min_part, lang=lang)
    return _collapse_duplicate_words(text)


_LINE_BREAK = re.compile(r"(\r\n|\n|\r)")


def _map_lines(text: str, transform) -> str:
    """Apply ``transform`` per line, keeping every newline in place.

    Rewriting a whole paragraph at once used to glue lines together, because the
    sentence splitter rejoined with spaces.
    """
    parts = _LINE_BREAK.split(text)
    out = []
    for part in parts:
        if _LINE_BREAK.fullmatch(part) or not part.strip():
            out.append(part)
            continue
        cleaned = transform(part)
        if not cleaned:
            out.append(part)
            continue
        lead = part[: len(part) - len(part.lstrip())]
        trail = part[len(part.rstrip()):]
        if lead and not cleaned.startswith(lead):
            cleaned = lead + cleaned.lstrip()
        if trail and not cleaned.endswith(trail):
            cleaned = cleaned.rstrip() + trail
        out.append(cleaned)
    return "".join(out)


def _rewrite_document(text: str, transform) -> str:
    """Protect first, then rewrite the prose line by line.

    Protection has to run on the whole document: a fenced code block or a
    ``\\begin{document}`` only makes sense across lines. The prose is still
    rewritten per line so the layout survives.
    """
    out = []
    for sp in split_protected(text):
        if sp.protected or not sp.text.strip():
            out.append(sp.text)
        else:
            out.append(_map_lines(sp.text, transform))
    return "".join(out)


def rewrite_text(text: str, strict: bool = False, seed: int = 0, lang: str = "auto", profile: str = "balanced") -> str:
    if not text:
        return text
    if lang == "auto":
        lang = detect_language(text)
    aggressive = profile == "aggressive"
    word_swaps = _rules(lang)[0]
    if aggressive:
        extra = EXTRA_WORD_SWAPS_TR if lang == "tr" else EXTRA_WORD_SWAPS_EN
        word_swaps = {**word_swaps, **extra}

    if profile == "conservative":
        selected = _break_chains(_pick_variants(word_swaps, random.Random(seed), lang))

        def transform(block: str) -> str:
            return _apply_word_swaps(block, selected, lang)
    else:
        def transform(block: str) -> str:
            return rewrite_free(block, strict=strict, seed=seed, lang=lang,
                                aggressive=aggressive)

    return _rewrite_document(text, transform)
