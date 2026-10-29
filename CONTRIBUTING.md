# Contributing to textscope

Thanks for taking the time to help. textscope is a small, dependency-free tool:
the rewriter is rule data plus deterministic string handling, and every
protected-zone claim is backed by a test. Contributions that keep that
property — data, narrow patterns, small functions, tests — are the easiest to
review and merge.

By participating you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).

## Development setup

Requirements: Python 3.10+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/mehmetefeaytas/textscope.git
cd textscope
uv sync --group dev        # creates .venv, installs pytest + ruff
uv pip install -e .        # installs the package and the `textscope` script
uv run pytest              # 147 tests
```

Run the CLI from the checkout with `uv run textscope ...` (or
`.venv/bin/textscope ...` after the editable install). The package has no
runtime dependencies; the optional `llm` extra (`uv sync --extra llm`) is only
needed for `--llm`.

## Quality bar

Both of these must pass before you open a pull request:

```bash
.venv/bin/python -m pytest -q            # 147 tests
.venv/bin/python -m ruff check src tests # lint, line length 100
```

CI runs the same two commands on Python 3.10–3.14 (`.github/workflows/ci.yml`),
so a change that only works on your local Python will fail there. There is no
separate formatter; ruff's defaults plus the 100-character limit in
`pyproject.toml` are the style.

Useful extras while working:

```bash
uv run python -c "from textscope.eval import evaluate, format_report; print(format_report(evaluate()))"
uv run textscope rewrite paper.tex --diff --dry-run
```

The quality gate rewrites a 27-sample bilingual corpus and must report
216/216 checks passing.

## How the rule tables work

`src/textscope/rules_en.py` and `src/textscope/rules_tr.py` are **plain data**.
They contain no logic beyond building dicts from pair lists, so a rule change
is reviewable as a diff of words, not code.

- English word swaps are declared in `_WORD_PAIRS_EN` and collapsed into
  `WORD_SWAPS_EN`; the aggressive additions live in `EXTRA_WORD_SWAPS_EN` and
  seed-driven alternatives in `WORD_VARIANTS_EN`.
- Turkish word swaps are declared in `_WORD_PAIRS_TR` and collapsed into
  `WORD_SWAPS_TR` (first occurrence wins if a duplicate slips in, which is why
  the duplicate test matters). `EXTRA_WORD_SWAPS_TR` and `WORD_VARIANTS_TR`
  follow the same pattern; `TR_STOPWORDS` is a separate frozenset used for
  language detection.
- Phrase swaps are `(regex, replacement)` pairs in `PHRASE_SWAPS_EN` /
  `PHRASE_SWAPS_TR`; contractions and leading transitions are separate tables.
- `rewrite.py` consumes these tables. At runtime `_break_chains()` drops any
  swap whose replacement is itself a key, and `--strict` filters out swaps that
  change the word count.

When you add a rule, it must satisfy all of the following invariants. They are
enforced by [`tests/test_rules_en.py`](tests/test_rules_en.py) and
[`tests/test_rules_tr.py`](tests/test_rules_tr.py); adding a rule that breaks
one of them should fail locally before it reaches CI.

1. **No duplicate keys.** Word pairs are lists specifically so a duplicate is
   visible; `test_no_duplicate_word_keys` compares the key list with its set.
   Do not "fix" a duplicate by relying on dict construction.
2. **No empty or no-op swaps.** Both sides must be non-empty, the key must
   differ from the value, keys must be lowercase and stripped, and replacements
   must be trimmed with no double spaces.
3. **Phrase patterns must compile, and replacements must not use
   backreferences.** `\1` / `\g<...>` make the output depend on the matched
   text, which makes the word-count and idempotency guarantees much harder to
   reason about. Turkish phrase patterns must also contain `\b`.
4. **A variant value must not itself be a swap key.** `WORD_VARIANTS_*` values
   are fed back into the same table; if a variant is a key, a second pass
   rewrites it again and the tool stops being idempotent. Variants must also
   reference an existing key and be unique.
5. **Never swap protected statistical vocabulary.** Words that carry a
   methods-section meaning are deliberately frozen. English:
   `significant`, `significantly`, `correlation`, `variable`, `variables`,
   `qualitative`, `quantitative`, `empirical`, `systematic`,
   `methodological`, `construct`, `intervention`, `interventions`, `hypothesis`,
   `sample`, `coefficient`, `regression`, `p-value`, `effect size`. Turkish:
   `anlamlı`, `istatistiksel`, `değişken`, `örneklem`, `güvenirlik`,
   `geçerlik`, `regresyon`, `katsayı`, `p değeri`, `etki büyüklüğü`. Also do
   not swap light-verb nouns bare (`analiz`, `yöntem`), because
   `analiz etmek` would become ungrammatical.
6. **Correct Turkish orthography.** Keys keep their Turkish letters
   (`kapsamlı`, `sürdürülebilir`, `literatür`); the ASCII-folded spelling must
   not appear as a separate key. Do not add circular pairs (`A → B` and
   `B → A`) and do not create English synonym chains (`A → B` where `B` is a
   key); both make output unstable.
7. **Keep the tables meaningful.** Aggressive extras must add a new key or
   deliberately override it with a different value; an exact duplicate of the
   base table is redundant. Minimum table sizes are asserted by the tests, so
   do not shrink a table to make a rule fit.

Phrase rules should be specific and word-bounded. A broad pattern such as
`\bthe\b` or an unanchored alternation rewrites prose it was never meant to
touch and is very hard to review.

## Adding a protected zone

Protected zones live in [`src/textscope/protected.py`](src/textscope/protected.py).
Most are entries in `_PROTECTED_RES`, a list of `(kind, compiled_regex)` pairs;
paired LaTeX environments are handled separately by the stack-based
`_latex_env_spans()` because a regex cannot match nesting.

To add a kind:

1. Pick a short, unique `kind` name. It appears in verification errors and in
   the `kind:index` hash keys, so it should describe the construct, not the
   rule number.
2. Write the **narrowest** pattern that matches the construct and nothing
   around it. Anchor it (`^`, `\A`, `\b`, a lookbehind), require the closing
   token, and avoid `[\s\S]*` unless the construct genuinely spans lines. A
   broad pattern wins the overlap resolution (matches are sorted by start, then
   longest first), so it can silently swallow neighbouring prose.
3. Verify the reassembly guarantee: for any document,
   `reassemble(split_protected(text)) == text` must hold byte for byte. The
   splitter copies ranges from the original string, so this holds by
   construction, but re-check it — a pattern that matches zero-width text or
   relies on a lookaround can still surprise you.
4. Add a test in [`tests/test_protected_extra.py`](tests/test_protected_extra.py).
   At minimum assert that the construct is recognised as protected, that
   surrounding prose is still rewritten, and that `rewrite_text()` leaves the
   construct byte-identical. A protection rule without a test is treated as a
   regression waiting to happen.
5. Run the full suite. `verify_protected()` re-splits the output, so a pattern
   that also matches generated text can turn a good rewrite into an abort
   (exit code 2). The quality gate is a good smoke test for that.

## Adding a format

Formats are detected in `detect_format()` in
[`src/textscope/formats.py`](src/textscope/formats.py), then routed in
`cli.py` (`_transform_text`, `_process_file`) and in `process_zip_file()`.
A new text format needs a mapping to `"txt"`-style handling plus an entry in
`SUPPORTED_EXTS`; a binary format needs a reader/writer that preserves
everything it does not rewrite, and a `verify_protected()` call on the
extracted text (see the `.docx` path). Cover both single-file and directory
processing in a test.

## Commit messages

Use the imperative mood and a short prefix:

```
feat: add ISBN-13 protected zone
fix: keep trailing punctuation outside URLs
docs: document the aggressive profile
test: cover nested LaTeX environments
chore: bump ruff
```

Keep the subject under ~72 characters. Explain *why* in the body when a change
is not obvious. Do not mix unrelated refactors into a rule-data PR.

## Reporting a rejected or incorrect rewrite

If `rewrite` aborts with `ABORT: protected zone violation` (exit code 2), or a
rewrite changes meaning, mangles grammar, or damages structure, open a bug with
the [bug report form](.github/ISSUE_TEMPLATE/bug_report.yml) and include:

- the smallest input that reproduces it (redact names, unpublished data and
  anything you cannot share),
- the exact command, including `--seed`, `--profile`, `--lang` and `--strict`,
- the output, or the `--diff` for the affected line,
- the `textscope --version` output (or
  `python -c "import textscope; print(textscope.__version__)"`).

A single sentence is usually enough. Please do not attach a full manuscript.
Disagreement about style or word choice is welcome too — say what the output
should have been, and whether the fix belongs in the rule data or in the
rewriter. Detector scores are not bug reports; see
[SECURITY.md](SECURITY.md#out-of-scope) for what the project does and does not
promise.
