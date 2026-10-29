# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Release status:** textscope has **not** been published to PyPI and no
> version has been tagged. The versions below group the commit history by
> feature set; `0.4.0` matches the current `pyproject.toml`. Dates are omitted
> because nothing has shipped yet.

## [0.4.0] - unreleased

### Added

- Quality gate (`textscope.eval`): a 27-sample bilingual corpus rewritten and
  checked for protected zones, structure, word budget, artifacts, language,
  idempotency and sentence fragments (216 checks).
- Idempotency enforcement: swap chains (`framework → structure → shape`) are
  broken at runtime, so rewriting an already-rewritten text is a no-op.
- Expanded English and Turkish rule tables, including aggressive extras and
  seed-driven variants.
- Additional protected zones: YAML front matter, markdown tables, HTML tags and
  comments, markdown link destinations, numeric and author-year citations,
  footnote markers and definitions, reference definitions, DOIs, ISBNs, arXiv
  IDs, semantic versions, HTML entities, emoji shortcodes and template
  placeholders (`{{ var }}`, `${VAR}`, `%s`).
- Code-file rewriting moved to a character scanner: only comments and
  docstrings are rewritten, and `#` inside strings, URLs with `#fragment`,
  shebangs and trailing comments are no longer misread.

### Fixed

- Structural regressions in sentence splitting, duplicate-word cleanup and
  line preservation.
- Protected-zone verification now covers the `.docx` path against the extracted
  text.

## [0.3.0] - unreleased

### Added

- `textscope serve`: a standard-library HTTP server exposing `clean`,
  `rewrite` and `check` over JSON. Binds to `127.0.0.1` and has no auth.
- `--in-place` for `clean`/`rewrite`, writing a `.bak` backup first.
- Optional LLM backend via `--llm provider:model` (`openai`, `anthropic`;
  installed with the `llm` extra), with the same post-rewrite protected-zone
  verification as the deterministic path.
- `textscope detect`: GPTZero integration, enabled by `GPTZERO_API_KEY`.
- PyPI publish workflow on `v*` tags.

### Changed

- README documents the new commands and options.

## [0.2.0] - unreleased

### Added

- Turkish language support: word, phrase and transition tables, `TR_STOPWORDS`,
  and suffix-aware verb softening (`-mektedir → -yor`, `-mıştır → -di`,
  `-acaktır → -acak`, `-malıdır → -malı`) with vowel harmony and t→d handling.
- Language detection that also recognises ASCII-only Turkish.
- `--profile conservative|balanced|aggressive` and `--seed` for deterministic
  variation.
- Language-aware metrics: rare-word ratio and sentence-length variance.
- LaTeX environment protection using a stack, so nested environments and
  `\begin{document}` are handled without swallowing the whole file.

### Changed

- Reordered the swap tables during the Turkish/profiles work.

## [0.1.0] - unreleased

### Added

- Initial implementation: `clean`, `rewrite` and `check`.
- Protected zones with SHA-256 verification; on a mismatch the command aborts
  with exit code 2 and writes nothing.
- Deterministic English word/phrase rewriting with `--strict` word-count
  preservation.
- Source-code support limited to comments and docstrings.
- Burstiness and type-token metrics.

### Fixed

- Leading spaces in comments are preserved when rewriting code files.
