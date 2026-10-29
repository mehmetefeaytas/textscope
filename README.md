# textscope

Clean and rewrite text so it no longer reads as AI-generated (Turnitin-style AI
detection), while guaranteeing that protected zones — code, equations, `\cite{}`,
URLs, numbers, string literals — are byte-identical before and after.

Zero runtime dependencies. Python 3.10+. Managed with `uv`.

## Features

- **Formats**: `.txt`, `.md`, `.tex`, `.docx`, source code (comments/docstrings only), `.zip` batches.
- **clean**: purge zero-width/Cf characters, NFC normalize, fix ligatures, normalize whitespace, dashes and quotes.
- **rewrite**: deterministic word/sentence-level rewrite. `--strict` keeps the word count exactly (delta = 0).
- **Protected zones**: code, math, `\cite{}`, URLs, numbers, string literals never change. SHA-256 verified before/after; on violation the write is aborted.
- **CLI**: `clean | rewrite | check`, `--dry-run`, `--diff`, `--json` report.
- **Metrics**: burstiness, type-token ratio, entropy, AI-pattern hit count.

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
- LaTeX commands (`\cite{}`, `\ref{}`, `\label{}`, ...)
- URLs and emails
- Numbers
- Source-code string literals (only comments/docstrings are rewritten in code files)

If any protected span changes, the command aborts with exit code 2 and writes nothing.

## Tests

```bash
uv sync --group dev
uv run pytest
```

CI runs on Python 3.10–3.14 (see `.github/workflows/ci.yml`).

## License

MIT
