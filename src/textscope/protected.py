from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass


@dataclass
class Span:
    text: str
    protected: bool
    kind: str = "text"


# Environments whose body is ordinary prose (so it must stay rewritable).
# `document` is deliberately excluded: protecting it would freeze the whole file.
_UNPROTECTED_ENVS = {"document"}

_LATEX_ENV_TOKEN = re.compile(r"\\(begin|end)\{([^}]+)\}")

_PROTECTED_RES = [
    # YAML/TOML front matter is only valid at the very start of the document.
    ("front_matter", re.compile(r"\A---[ \t]*\r?\n[\s\S]*?\r?\n---[ \t]*(?=\r?\n|\Z)")),
    ("html_comment", re.compile(r"<!--[\s\S]*?-->")),
    ("fence", re.compile(r"```[\s\S]*?```", re.MULTILINE)),
    ("math_display", re.compile(r"\$\$[\s\S]*?\$\$")),
    ("math_bracket", re.compile(r"\\\[[\s\S]*?\\\]")),
    ("math_paren", re.compile(r"\\\([\s\S]*?\\\)", re.DOTALL)),
    ("math_inline", re.compile(r"(?<!\\)\$[^$\n]+?\$")),
    ("inline_code", re.compile(r"`[^`\n]+`")),
    # Last character must not be sentence punctuation, so the period after a URL
    # stays in the rewritable prose.
    ("url", re.compile(r"https?://[^\s)>\]]*[A-Za-z0-9/#_=~%-]")),
    ("email", re.compile(r"\b[\w.+-]+@[\w.-]+\.\w+\b")),
    ("latex_cmd", re.compile(
        r"\\(?:cite|citet|citep|ref|eqref|label|bibliography|includegraphics|input|include|usepackage|documentclass|begin|end|section|subsection|subsubsection|title|author|date|maketitle|newcommand|renewcommand|frac|sqrt|sum|int|lim|intertext|text|mathrm|mathbf|mathit|mathcal|left|right|Big|big|Bigg|bigg|times|cdot|ldots|cdots|dots|alpha|beta|gamma|delta|epsilon|theta|lambda|mu|sigma|pi|omega|rho|phi|psi|tau|nu|xi|zeta|eta|kappa|upsilon|chi|iota|partial|nabla|infty|forall|exists|in|subset|subseteq|supset|supseteq|cup|cap|setminus|emptyset|varnothing|approx|neq|leq|geq|equiv|cong|sim|propto|to|rightarrow|leftarrow|Rightarrow|Leftarrow|leftrightarrow|mapsto|implies|iff|land|lor|neg|wedge|vee|cdot|times|div|pm|mp|circ|bullet|star|dagger|ddagger)\b(?:\[[^\]]*\])*(?:\{[^}]*\})*"
    )),
    ("latex_backslash", re.compile(r"\\[a-zA-Z]+")),
    # A "%" is only treated as a LaTeX comment when it starts the line. Treating
    # every "%" as a comment would swallow prose like "42% of students".
    ("latex_comment", re.compile(r"^[ \t]*%.*$", re.MULTILINE)),
    # Markdown table rows: keep pipes and alignment intact.
    ("md_table", re.compile(r"^[ \t]*\|[^\n]*$", re.MULTILINE)),
    # Markdown inline links/images: protect the destination only.
    ("md_link_target", re.compile(r"(?<=\])\([^)\s]+\)")),
    # Reference-style citations: [1], [12], [1, 2], [1-3].
    ("citation_index", re.compile(r"\[\d{1,3}(?:\s*[-,–]\s*\d{1,3})*\]")),
    # Author-year citations: (Smith, 2020), (Smith et al., 2020), (Smith & Jones 2019).
    ("citation_year", re.compile(
        r"\([A-ZÇĞİÖŞÜ][\wçğıöşü'.-]+"
        r"(?:\s+(?:et\s+al\.?|ve\s+ark\.?|&\s*[A-ZÇĞİÖŞÜ][\wçğıöşü'.-]+"
        r"|and\s+[A-ZÇĞİÖŞÜ][\wçğıöşü'.-]+))"
        r"*\s*,\s*\d{4}[a-z]?\)"
    )),
    ("citation_year_narrative", re.compile(
        r"\b[A-ZÇĞİÖŞÜ][\wçğıöşü'.-]+\s+et\s+al\.\s*\(\d{4}[a-z]?\)"
    )),
    # HTML/XML tags (opening, closing, self-closing); escaped "\<" is not a tag.
    ("html_tag", re.compile(r"(?<!\\)</?[A-Za-z][A-Za-z0-9:_-]*(?:\s+[^<>]*)?/?>")),
    ("number", re.compile(r"\b\d[\d,\.]*\b")),
]


def _latex_env_spans(text: str) -> list[tuple[int, int]]:
    """Match ``\\begin{env}`` … ``\\end{env}`` pairs with a stack.

    A regex cannot do this correctly: a non-greedy pattern stops at the *first*
    ``\\end{...}``, which turns ``\\begin{document}`` … ``\\end{equation}`` into one
    giant "protected" block. Nesting is resolved by the stack instead.
    """
    spans: list[tuple[int, int]] = []
    stack: list[tuple[str, int]] = []
    for m in _LATEX_ENV_TOKEN.finditer(text):
        kind, name = m.group(1), m.group(2)
        if name in _UNPROTECTED_ENVS:
            continue
        if kind == "begin":
            stack.append((name, m.start()))
            continue
        for i in range(len(stack) - 1, -1, -1):
            if stack[i][0] == name:
                spans.append((stack[i][1], m.end()))
                del stack[i:]
                break
    return spans


def split_protected(text: str) -> list[Span]:
    matches = []
    for kind, rx in _PROTECTED_RES:
        for m in rx.finditer(text):
            matches.append((m.start(), m.end(), kind, m.group(0)))
    for start, end in _latex_env_spans(text):
        matches.append((start, end, "latex_env", text[start:end]))
    if not matches:
        return [Span(text=text, protected=False, kind="text")] if text else []
    matches.sort(key=lambda x: (x[0], -(x[1] - x[0])))
    chosen = []
    cur_end = -1
    for s, e, kind, t in matches:
        if s >= cur_end:
            chosen.append((s, e, kind, t))
            cur_end = e
    spans = []
    pos = 0
    for s, e, kind, t in chosen:
        if s > pos:
            spans.append(Span(text=text[pos:s], protected=False, kind="text"))
        spans.append(Span(text=text[s:e], protected=True, kind=kind))
        pos = e
    if pos < len(text):
        spans.append(Span(text=text[pos:], protected=False, kind="text"))
    spans = [sp for sp in spans if sp.text != "" or sp.protected]
    return spans


def reassemble(spans: list[Span]) -> str:
    return "".join(s.text for s in spans)


def protected_hashes(text: str) -> dict[str, str]:
    spans = split_protected(text)
    out = {}
    idx = 0
    for sp in spans:
        if sp.protected:
            out[f"{sp.kind}:{idx}"] = hashlib.sha256(sp.text.encode("utf-8")).hexdigest()
            idx += 1
    return out


def verify_protected(original: str, result: str) -> tuple[bool, list[str]]:
    o_spans = split_protected(original)
    r_spans = split_protected(result)
    o_prot = [sp.text for sp in o_spans if sp.protected]
    r_prot = [sp.text for sp in r_spans if sp.protected]
    errors = []
    if len(o_prot) != len(r_prot):
        errors.append(f"protected span count changed: {len(o_prot)} -> {len(r_prot)}")
        return False, errors
    for i, (a, b) in enumerate(zip(o_prot, r_prot)):
        if a != b:
            errors.append(f"protected span {i} changed")
    o_hashes = list(protected_hashes(original).values())
    r_hashes = list(protected_hashes(result).values())
    if o_hashes != r_hashes and not errors:
        errors.append("protected hash mismatch")
    return len(errors) == 0, errors
