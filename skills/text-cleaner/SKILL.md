---
name: text-cleaner
description: Clean and rewrite text to evade AI detection (Turnitin-style) while preserving protected zones (code, LaTeX, URLs, numbers, strings). Use when the user wants to humanize AI-generated text, clean invisible characters, normalize text, or test whether text passes AI detectors.
---

# text-cleaner

Use the `textscope` CLI to clean and rewrite text so it no longer reads as AI-generated,
while guaranteeing that protected zones (code, equations, `\cite{}`, URLs, numbers, string
literals) are byte-identical before and after.

## Install

```bash
cd /path/to/textscope
uv sync
uv pip install -e .
```

## Commands

- `textscope clean INPUT -o OUT` — purge zero-width/Cf chars, NFC, ligatures, whitespace, dashes/quotes.
- `textscope rewrite INPUT -o OUT [--strict] [--seed N]` — word/sentence-level rewrite.
  - `--strict` keeps the word count exactly equal (delta = 0).
- `textscope check INPUT` — metrics + AI-pattern hit count.
- `--dry-run`, `--diff`, `--json` supported.

## Protected zones

Numbers, URLs, emails, LaTeX commands (`\cite{}`, `\ref{}`, math `$...$`), fenced/inline code,
and code comments/docstrings are protected. `verify_protected` aborts the write on any violation.

## Turnitin verification workflow (mandatory)

To confirm a rewritten text passes Turnitin AI detection, run:

1. `textscope rewrite input.txt --strict -o out.txt`
2. `textscope check out.txt` — expect `ai_pattern_total` low and `burstiness_cv` >= 0.25.
3. Verify protected zones: `textscope check` + manual diff (`--diff`).
4. Paste `out.txt` into at least two independent AI detectors (e.g. ZeroGPT, GPTZero,
   Copyleaks) and record scores. Target: < 20% AI probability.
5. If score too high, adjust `--seed`, re-run, re-test. Iterate until pass.
6. Never edit protected zones; abort if `protected_ok` is false.

## Metrics targets

- burstiness_cv (sentence-length coefficient of variation) >= 0.25
- type_token_ratio >= 0.6
- trigram_repetition <= 0.05
- ai_pattern_total <= 2
