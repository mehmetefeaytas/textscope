---
name: turnitin-tester
description: Test whether text produced by textscope passes Turnitin-style AI detection. Runs local metrics, independent detectors via browser, and protected-zone checks. Use when validating textscope output.
---

# turnitin-tester

Validate that a textscope output passes AI detection.

## Steps

1. Ensure `textscope` is installed (`uv pip install -e .`).
2. Run `textscope check FILE --json` and capture the local metrics.
3. Run `textscope rewrite FILE --dry-run --json` and read `protected_ok`, `word_count_delta`.
4. Thresholds (fail if not met) — these are **local proxies only**, not a Turnitin verdict:
   - `burstiness_cv >= 0.25`
   - `type_token_ratio >= 0.6`
   - `ai_pattern_total <= 2` (count of known clichés, not a detector score)
   - `protected_ok == true`
5. Open ZeroGPT and GPTZero in a browser; paste the file; record AI %.
6. If AI % >= 20, retry with `--seed 1..5`, `--profile aggressive` or `--strict` and re-test.
7. Report every score, the seed and the profile used, plus a manual readability pass.
   A low AI % with broken grammar is a failure, not a pass.
