from __future__ import annotations

import re
import unicodedata

from .protected import Span, reassemble, split_protected

# Zero-width / format characters to purge
_ZERO_WIDTH = {
    "\u200b", "\u200c", "\u200d", "\u200e", "\u200f",
    "\u202a", "\u202b", "\u202c", "\u202d", "\u202e",
    "\u2060", "\u2061", "\u2062", "\u2063", "\u2064",
    "\ufeff", "\u00ad", "\u180e", "\u2000", "\u2001",
}

_LIGATURES = {
    "\ufb00": "ff", "\ufb01": "fi", "\ufb02": "fl", "\ufb03": "ffi",
    "\ufb04": "ffl", "\ufb05": "st", "\ufb06": "st",
    "\u0132": "IJ", "\u0133": "ij", "\u0152": "OE", "\u0153": "oe",
    "\u0149": "'n", "\u017f": "s",
}

_QUOTE_MAP = {
    "\u201c": '"', "\u201d": '"', "\u201e": '"', "\u201f": '"',
    "\u2033": '"', "\u2036": '"', "\u00ab": '"', "\u00bb": '"',
    "\u2018": "'", "\u2019": "'", "\u201a": "'", "\u201b": "'",
    "\u2032": "'", "\u2035": "'",
}

_DASH_MAP = {
    "\u2010": "-", "\u2011": "-", "\u2012": "-", "\u2013": "-",
    "\u2014": "-", "\u2015": "-", "\u2212": "-", "\u2043": "-",
    "\u2016": "|",
}

_NBSP = "\u00a0"


def _clean_free(text: str) -> str:
    # Remove zero-width / format chars (Cf category too)
    out = []
    for ch in text:
        if ch in _ZERO_WIDTH:
            continue
        if unicodedata.category(ch) == "Cf":
            continue
        out.append(ch)
    text = "".join(out)
    # NFC
    text = unicodedata.normalize("NFC", text)
    # Ligatures
    for k, v in _LIGATURES.items():
        text = text.replace(k, v)
    # Quotes
    for k, v in _QUOTE_MAP.items():
        text = text.replace(k, v)
    # Dashes
    for k, v in _DASH_MAP.items():
        text = text.replace(k, v)
    # NBSP -> space
    text = text.replace(_NBSP, " ")
    # Collapse whitespace: trailing spaces per line
    lines = text.split("\n")
    lines = [ln.rstrip() for ln in lines]
    text = "\n".join(lines)
    # Collapse 3+ newlines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse multiple spaces (but not newlines) to single
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text


def clean_text(text: str) -> str:
    spans = split_protected(text)
    new_spans = []
    for i, sp in enumerate(spans):
        if sp.protected:
            new_spans.append(sp)
            continue
        original = sp.text
        cleaned = _clean_free(original)
        prev_protected = (i > 0 and spans[i - 1].protected)
        next_protected = (i + 1 < len(spans) and spans[i + 1].protected)
        if prev_protected and original.startswith((" ", "\t")) and not cleaned.startswith((" ", "\t")):
            cleaned = " " + cleaned
        if next_protected and original.endswith((" ", "\t")) and not cleaned.endswith((" ", "\t")):
            cleaned = cleaned + " "
        new_spans.append(Span(text=cleaned, protected=False, kind="text"))
    result = reassemble(new_spans)
    # strip trailing spaces at end of each line (safety) but keep protected boundaries already handled
    lines = result.split("\n")
    lines = [ln.rstrip(" ") for ln in lines]
    return "\n".join(lines)
