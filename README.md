# textscope

Clean and rewrite text so it no longer reads as AI-generated (Turnitin-style AI
detection), while guaranteeing that protected zones — code, equations, `\cite{}`,
URLs, numbers, string literals — are byte-identical before and after.

Zero runtime dependencies. Python 3.10+. Managed with `uv`.

## Features

- **Formats**: `.txt`, `.md`, `.tex`, `.docx`, source code (comments/docstrings only), `.zip` batches.
- **clean**: purge zero-width/Cf characters, NFC normalize, fix ligatures, normalize whitespace, dashes and quotes.
- **rewrite**: deterministic word/sentence-level rewrite. `--strict` keeps the word count exactly (delta = 0).
- **Structure-safe**: line breaks, blank lines and paragraph layout survive; rewriting happens per line, never as a document-wide reflow.
- **Protected zones**: code, math, `\cite{}`, URLs, numbers, string literals never change. SHA-256 verified before/after; on violation the write is aborted. LaTeX environments are matched with a stack, so nesting and `\begin{document}` work. Also protected: YAML front matter, markdown tables, HTML tags and comments, markdown link destinations, `[1]`/`[4-6]` citation markers, `(Smith et al., 2020)` author-year citations, LaTeX `%` comments (only at line start, so `42%` stays prose).
- **English** (626 word swaps, 184 phrase swaps, 73 transitions, 65 contractions): `a/an` repair, irregular-verb agreement (`have shown`, not `have showed`), repeated-starter cleanup. Statistical terms (`significant`, `correlation`, `variable`, `qualitative`) are deliberately left alone so findings keep their meaning.
- **Turkish** (213 word swaps, 141 phrase swaps, 54 transitions): suffix-aware verb softening (`-mektedir` → `-yor`, `-mıştır` → `-di`, `-acaktır` → `-acak`, `-malıdır` → `-malı`) with vowel harmony and t→d handling, plus light-verb phrase rules (`analiz edilmesini` → `incelenmesini`). Language detection works even on ASCII-only Turkish (`Bu calisma ...`).
- **Rule data is testable**: rules live in `rules_en.py` / `rules_tr.py` as plain data, guarded by integrity tests (no duplicate keys, no no-op swaps, every regex compiles, no synonym chains, correct Turkish orthography).
- **Code files**: a character scanner rewrites only comments and docstrings — trailing comments included — and never touches strings, URLs with `#fragment`, or shebangs.
- **CLI**: `clean | rewrite | check | serve`, `--dry-run`, `--diff`, `--json` report, `--seed` (variation), `--profile`.
- **Metrics**: burstiness, type-token ratio, entropy, AI-pattern hit count.

### Profiles and seeds

| Flag | Effect |
| --- | --- |
| `--profile conservative` | word swaps only; phrases and sentence flow untouched |
| `--profile balanced` | word + phrase swaps, transition cleanup, contractions, sentence splitting |
| `--profile aggressive` | balanced plus a larger swap table and longer-sentence splitting |
| `--seed N` | picks synonym variants deterministically: same seed = same output, different seed = different output |

### Turkish specifics

Turkish is agglutinative, so a plain word list is not enough. Besides the word
and phrase tables, formal verb endings are rewritten generically while keeping
one word → one word (so `--strict` still holds):

| Input | Output |
| --- | --- |
| `göstermektedir` | `gösteriyor` |
| `yapılmaktadır` | `yapılıyor` |
| `etmektedir` | `ediyor` |
| `okumaktadır` | `okuyor` |
| `incelenmiştir` | `incelendi` |
| `yapılmıştır` | `yapıldı` |
| `olacaktır` | `olacak` |
| `yapılmalıdır` | `yapılmalı` |

Uppercase handling is Turkish-aware (`i` → `İ`), so sentence starts stay correct.

## Install

```bash
git clone https://github.com/mehmetefeaytas/textscope.git
cd textscope
uv sync
uv pip install -e .
```

## Usage

```bash
# Clean invisible characters / normalize
textscope clean input.txt -o clean.txt

# Rewrite (humanize)
textscope rewrite input.txt -o out.txt

# Strict: word count preserved exactly
textscope rewrite input.txt --strict -o out.txt

# Turkish
textscope rewrite input.txt --lang tr -o out.txt

# Profile
textscope rewrite input.txt --profile aggressive -o out.txt

# Variation: different seed, different wording (same seed = reproducible)
textscope rewrite input.txt --seed 3 -o out.txt

# Optional LLM backend
textscope rewrite input.txt --llm openai:gpt-4o-mini -o out.txt

# In-place (backup .bak)
textscope rewrite input.txt --in-place

# HTTP server
textscope serve --port 8765

# External detector (needs GPTZERO_API_KEY)
textscope detect out.txt

# Inspect metrics
textscope check out.txt

# Diff
textscope rewrite input.txt --diff

# JSON report
textscope rewrite input.txt --json -o out.txt

# Dry run
textscope clean input.txt --dry-run
```

## Batch / DOCX / ZIP

```bash
textscope rewrite paper.tex -o paper_rw.tex
textscope rewrite report.docx -o report_rw.docx
textscope rewrite archive.zip -o archive_rw.zip
textscope rewrite src/ -o outdir/   # directory (recursive)
```

## Protected zones

The following are never modified and are SHA-256 verified:

- Fenced and inline code
- Math (`$...$`, `$$...$$`, `\[...\]`, `\(...\)`)
- LaTeX commands (`\cite{}`, `\ref{}`, `\label{}`, ...) and LaTeX environments
- URLs and emails
- Numbers
- Source-code string literals (only comments/docstrings are rewritten in code files)
- YAML/TOML front matter at the start of a document
- Markdown table rows, and the destination half of `[text](target)`
- HTML/XML tags and `<!-- comments -->`
- Citation markers `[1]`, `[2, 3]`, `[4-6]`
- Author-year citations such as `(Smith et al., 2020)` and `Smith et al. (2020)`
- LaTeX `%` line comments — only when `%` starts the line, so `42% of students` stays prose

If any protected span changes, the command aborts with exit code 2 and writes nothing.

## Limitations

Be honest about what this does and does not do:

- It is a **deterministic word/phrase rewriter**, not a paraphraser. It swaps a fixed
  list of AI-typical words and flattens some phrases; it does not restructure
  arguments or regenerate sentences.
- It therefore **cannot guarantee** that a text passes Turnitin, GPTZero or any other
  detector. Those tools score token-level perplexity and burstiness, not the presence
  of specific words. `textscope check` reports local proxies only; the `ai_pattern_total`
  number is a count of known clichés, not a detection probability.
- Some swaps can still change nuance ("facilitate nuanced outputs" → "help subtle
  outputs"). Always read the diff (`--diff`) before submitting anything.
- `detect` needs a paid `GPTZERO_API_KEY`; there is no offline detector.
- Not a substitute for actually writing the text. Using it to misrepresent authorship
  may violate your institution's academic-integrity rules.

## Tests

```bash
uv sync --group dev
uv run pytest
```

101 tests covering the rewriter, protected zones, code-comment handling, and the
rule-data integrity (duplicate keys, no-op swaps, regex compilation, synonym chains,
Turkish orthography).

CI runs on Python 3.10–3.14 (see `.github/workflows/ci.yml`).

## License

MIT
