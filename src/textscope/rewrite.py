from __future__ import annotations

import random
import re

from .protected import Span, reassemble, split_protected

# AI-ish word -> human-ish synonym (1:1)
WORD_SWAPS = {
    "delve": "explore",
    "delving": "exploring",
    "tapestry": "mix",
    "multifaceted": "complex",
    "nuanced": "subtle",
    "pivotal": "key",
    "crucial": "important",
    "vital": "essential",
    "paramount": "top",
    "underscore": "highlight",
    "foster": "build",
    "bolster": "boost",
    "leverage": "use",
    "utilize": "use",
    "utilizes": "uses",
    "utilized": "used",
    "utilizing": "using",
    "facilitate": "help",
    "streamline": "simplify",
    "robust": "strong",
    "comprehensive": "full",
    "meticulous": "careful",
    "seamless": "smooth",
    "groundbreaking": "new",
    "transformative": "big",
    "paradigm": "model",
    "synergy": "teamwork",
    "holistic": "whole",
    "ecosystem": "system",
    "landscape": "field",
    "realm": "area",
    "plethora": "many",
    "myriad": "many",
    "embark": "start",
    "navigate": "handle",
    "harness": "use",
    "spearhead": "lead",
    "champion": "support",
    "elevate": "raise",
    "empower": "enable",
    "unlock": "open",
    "unleash": "release",
    "revolutionize": "change",
    "optimize": "improve",
    "furthermore": "also",
    "moreover": "also",
    "additionally": "also",
    "consequently": "so",
    "therefore": "so",
    "nevertheless": "still",
    "nonetheless": "still",
    "ultimately": "finally",
    "significantly": "notably",
    "notably": "notably",
    "importantly": "key",
    "interestingly": "oddly",
    "surprisingly": "surprisingly",
}

# Phrase swaps (may change word count) - applied in non-strict
PHRASE_SWAPS = [
    (r"\bit is important to note that\b", "note that"),
    (r"\bit is worth noting that\b", "note that"),
    (r"\bit should be noted that\b", "note that"),
    (r"\bit is worth mentioning that\b", "note that"),
    (r"\bplays a crucial role in\b", "matters for"),
    (r"\bplays a vital role in\b", "matters for"),
    (r"\bplays a key role in\b", "matters for"),
    (r"\bserves as a\b", "is a"),
    (r"\bserves as an\b", "is an"),
    (r"\ba wide range of\b", "many"),
    (r"\ba variety of\b", "various"),
    (r"\bin order to\b", "to"),
    (r"\bdue to the fact that\b", "because"),
    (r"\bin spite of the fact that\b", "although"),
    (r"\bat this point in time\b", "now"),
    (r"\bin the event that\b", "if"),
    (r"\bfor the purpose of\b", "to"),
    (r"\bwith regard to\b", "about"),
    (r"\bin terms of\b", "in"),
    (r"\bon the basis of\b", "based on"),
    (r"\bas a matter of fact\b", "in fact"),
    (r"\bin light of the fact that\b", "since"),
    (r"\bwith respect to\b", "about"),
    (r"\bin the context of\b", "in"),
    (r"\bat the end of the day\b", "ultimately"),
    (r"\bfirst and foremost\b", "first"),
]

# Leading transition removal (non-strict): replace transition + comma with empty
LEADING_TRANSITIONS = [
    "moreover", "furthermore", "additionally", "in addition",
    "consequently", "therefore", "thus", "hence",
    "nevertheless", "nonetheless", "however", "meanwhile",
    "in conclusion", "to conclude", "in summary", "to summarize",
    "in essence", "ultimately", "overall", "importantly",
    "notably", "significantly", "interestingly", "surprisingly",
    "on the other hand", "on the contrary",
]

CONTRACTIONS = [
    (r"\bdo not\b", "don't"),
    (r"\bcannot\b", "can't"),
    (r"\bcan not\b", "can't"),
    (r"\bit is\b", "it's"),
    (r"\bthat is\b", "that's"),
    (r"\bwe are\b", "we're"),
    (r"\bthey are\b", "they're"),
    (r"\byou are\b", "you're"),
    (r"\bi am\b", "I'm"),
    (r"\bwill not\b", "won't"),
    (r"\bis not\b", "isn't"),
    (r"\bare not\b", "aren't"),
    (r"\bwas not\b", "wasn't"),
    (r"\bwere not\b", "weren't"),
    (r"\bhas not\b", "hasn't"),
    (r"\bhave not\b", "haven't"),
    (r"\bhad not\b", "hadn't"),
    (r"\bdoes not\b", "doesn't"),
    (r"\bdid not\b", "didn't"),
    (r"\blet us\b", "let's"),
]


def _preserve_case(original: str, replacement: str) -> str:
    if original and original[0].isupper():
        return replacement[0].upper() + replacement[1:] if replacement else replacement
    return replacement


def _apply_word_swaps(text: str, strict: bool) -> str:
    def repl(m):
        w = m.group(0)
        low = w.lower()
        if low in WORD_SWAPS:
            r = WORD_SWAPS[low]
            return _preserve_case(w, r)
        return w
    # Build regex of all keys
    if not WORD_SWAPS:
        return text
    pattern = r"\b(" + "|".join(re.escape(k) for k in WORD_SWAPS) + r")\b"
    return re.sub(pattern, repl, text, flags=re.IGNORECASE)


def _apply_phrase_swaps(text: str) -> str:
    for pat, rep in PHRASE_SWAPS:
        def repl(m, rep=rep):
            return _preserve_case(m.group(0), rep)
        text = re.sub(pat, repl, text, flags=re.IGNORECASE)
    return text


def _remove_leading_transitions(text: str) -> str:
    # Per sentence
    sentences = re.split(r"(?<=[.!?])\s+", text)
    out = []
    for s in sentences:
        s2 = s
        for tr in LEADING_TRANSITIONS:
            # match transition at start followed by comma or space
            m = re.match(r"\s*" + re.escape(tr) + r"\b\s*,?\s*", s2, flags=re.IGNORECASE)
            if m:
                # remove only if followed by content
                rest = s2[m.end():]
                if rest.strip():
                    # if comma removed, keep space
                    s2 = rest
                    # ensure first char capitalized
                    if s2 and s2[0].islower():
                        s2 = s2[0].upper() + s2[1:]
                break
        out.append(s2)
    return " ".join(out)


def _apply_contractions(text: str) -> str:
    for pat, rep in CONTRACTIONS:
        text = re.sub(pat, rep, text, flags=re.IGNORECASE)
    return text


def _split_long_sentences(text: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    out = []
    for s in sentences:
        words = s.split()
        if len(words) > 10:
            # split at first comma if possible
            ci = s.find(",")
            if ci > 8 and ci < len(s) - 5:
                left = s[:ci] + "."
                right = s[ci+1:].strip()
                if right and right[0].islower():
                    right = right[0].upper() + right[1:]
                if not right.endswith((".", "!", "?")):
                    right = right + "."
                out.append(left)
                out.append(right)
                continue
            # try split at a comma followed by conjunction
            m = re.search(r",\s+(and|but|which|while|although|because|or|so)\s+", s)
            if m:
                left = s[:m.start()] + "."
                right = s[m.end():]
                if right and right[0].islower():
                    right = right[0].upper() + right[1:]
                # ensure right ends with punctuation
                if not right.endswith((".", "!", "?")):
                    right = right + "."
                # remove trailing period duplicate on left? left already has .
                out.append(left)
                out.append(right)
                continue
            # split at first " and " / " but " / " because "
            for conj in [" and ", " but ", " because ", " although ", " while "]:
                idx = s.lower().find(conj)
                if idx > 5 and idx < len(s) - 5:
                    left = s[:idx] + "."
                    right = s[idx + len(conj):]
                    if right and right[0].islower():
                        right = right[0].upper() + right[1:]
                    if not right.endswith((".", "!", "?")):
                        right = right + "."
                    out.append(left)
                    out.append(right)
                    break
            else:
                out.append(s)
            continue
        out.append(s)
    return " ".join(out)

def _vary_sentence_lengths(text: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    out = []
    i = 0
    while i < len(sentences):
        s = sentences[i].strip()
        if not s:
            i += 1
            continue
        if False:
            nxt = sentences[i + 1].strip()
            if nxt:
                # merge: drop period of s, append nxt with lowercase start
                left = s.rstrip(".!?")
                if nxt and nxt[0].isupper():
                    nxt = nxt[0].lower() + nxt[1:]
                merged = left + ", " + nxt
                out.append(merged)
                i += 2
                continue
        out.append(s)
        i += 1
    return " ".join(out)

def rewrite_free(text: str, strict: bool = False, seed: int = 0) -> str:
    if not text.strip():
        return text
    random.Random(seed)
    original_text = text

    # Word swaps (both modes)
    text = _apply_word_swaps(text, strict)

    if not strict:
        text = _apply_phrase_swaps(text)
        text = _remove_leading_transitions(text)
        text = _apply_contractions(text)
        text = _split_long_sentences(text)
        text = _vary_sentence_lengths(text)
    else:
        # strict: only 1:1 swaps; also light transition word swap already in WORD_SWAPS? 
        # Remove leading transitions by replacing with empty would change count; skip in strict.
        pass

    # Ensure word count preserved in strict mode
    if strict and len(text.split()) != len(original_text.split()):
        text = original_text
        text = _apply_word_swaps(text, strict)
        if len(text.split()) != len(original_text.split()):
            text = original_text
    return text


def rewrite_text(text: str, strict: bool = False, seed: int = 0) -> str:
    spans = split_protected(text)
    new_spans = []
    for i, sp in enumerate(spans):
        if sp.protected:
            new_spans.append(sp)
            continue
        original = sp.text
        cleaned = rewrite_free(original, strict=strict, seed=seed)
        prev_protected = (i > 0 and spans[i - 1].protected)
        next_protected = (i + 1 < len(spans) and spans[i + 1].protected)
        if prev_protected and original.startswith((" ", "\t")) and not cleaned.startswith((" ", "\t")):
            cleaned = " " + cleaned
        if next_protected and original.endswith((" ", "\t")) and not cleaned.endswith((" ", "\t")):
            cleaned = cleaned + " "
        new_spans.append(Span(text=cleaned, protected=False, kind="text"))
    return reassemble(new_spans)
