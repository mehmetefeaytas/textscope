---
name: turnitin-tester
description: Test whether text produced by textscope passes Turnitin-style AI detection. Runs local metrics, independent detectors via browser, and protected-zone checks. Use when validating textscope output.
---

# turnitin-tester

Validate that a textscope output passes AI detection.

## Steps

1. Ensure `textscope` is installed (`uv pip install -e .`).
2. Run `textscope check FILE --json` and capture metrics.
3. Thresholds (fail if not met):
   - burstiness_cv >= 0.25
   - type_token_ratio >= 0.6
   - ai_pattern_total <= 2
   - protected_ok == true (run `textscope rewrite ... --diff` dry-run)
4. Open ZeroGPT and GPTZero in browser; paste the file; record AI %.
5. Pass criterion: AI % < 20 on both.
6. If fail, try `--seed` 1..5 and `--strict`/non-strict; re-test.
7. Report final scores and seed used.
