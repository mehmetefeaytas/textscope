# Security Policy

textscope processes documents locally, but it is not a sandbox: it reads files,
writes files, parses `.docx`/`.zip` archives, and has an optional HTTP
server. This page explains what is supported, how to report a problem
privately, and which behaviours are deliberate.

## Supported versions

| Version | Supported |
| --- | --- |
| 0.4.x | ✅ |
| < 0.4 | ❌ |

The project has not been published to PyPI yet, so "version" means the
`version` field in [`pyproject.toml`](pyproject.toml) (or
`textscope.__version__`) of the checkout you are running. Security fixes land on
`main`; older snapshots are not maintained.

## Reporting a vulnerability

Please **do not open a public issue** for a suspected vulnerability. Email
[mehmetefeaytas@icloud.com](mailto:mehmetefeaytas@icloud.com) with the subject
`textscope security` and include:

- the affected version and Python version,
- the smallest input and command that reproduces the problem,
- what an attacker gains (data disclosure, file overwrite, code execution,
  denial of service),
- any suggested fix, if you have one.

You will get an acknowledgement on a best-effort basis; this is a
single-maintainer project, so please allow a few days. Once a fix is ready and
released, you are welcome to publish the details — credit is given unless you
ask otherwise. Do not include private manuscripts or third-party personal data
in the report; a synthetic reproducer is enough.

## In scope

- **Text exfiltration.** Any code path that sends document text to a network
  service without an explicit, visible opt-in. The core `clean`, `rewrite` and
  `check` paths, the file transforms, and the protected-zone verifier must stay
  offline. The opt-ins are `textscope detect` (sends text to GPTZero when
  `GPTZERO_API_KEY` is set), `rewrite --llm` (sends text to the chosen
  provider), and `serve` (accepts text over HTTP).
- **Protected-zone bypass.** Any input for which a protected construct (code,
  math, `\cite{}`, URL, number, DOI, citation, front matter, and the rest of
  the list in `protected.py`) is modified without the command aborting with a
  non-zero exit code. Include the input and the resulting diff.
- **Archive and path handling.** Zip-slip or path traversal through `.zip`
  entry names, `.docx` package parts, or directory output (`-o`), including
  absolute paths, `..` segments, symlinks and entries that escape the output
  directory. Also report crashes or unbounded memory use triggered by a
  malformed archive.
- **Unsafe `serve` exposure.** The server has no authentication, no TLS, no
  request-size limit and no rate limiting. It binds to `127.0.0.1` by default
  for that reason. A report is in scope if the defaults can be bypassed (for
  example, a request that escapes the intended local-only binding) or if a
  request can read or write files outside the request body. Running
  `textscope serve --host 0.0.0.0` behind a proxy without adding authentication
  is a deployment decision, not a vulnerability — but tell us if the docs make
  that look safe when it is not.

> **Warning:** `textscope serve` is a local development helper. It speaks
> plain HTTP, accepts any client that can reach the port, and has no auth.
> Never expose it to a public network, and do not put it behind a reverse proxy
> without authentication and TLS.

## Out of scope

- **AI-detector evasion results.** textscope is a deterministic word/phrase
  rewriter. It does not guarantee that a text passes Turnitin, GPTZero or any
  other detector, and a low score is not a bug. `check` reports local proxies
  (`ai_pattern_total` is a count of known clichés, not a probability).
- **Rule quality and style opinions.** A swap that reads awkwardly, a missing
  synonym, or a disagreement about tone belongs in the
  [bug report](.github/ISSUE_TEMPLATE/bug_report.yml) or
  [feature request](.github/ISSUE_TEMPLATE/feature_request.yml) flow. It is not
  a security issue unless it breaks a protected zone or leaks text.
- **Misuse and academic policy.** Using the tool to misrepresent authorship may
  violate your institution's rules. That is the user's responsibility.
- **Third-party services.** What GPTZero or an LLM provider does with text you
  choose to send them is governed by their policies. Report provider-side
  issues to the provider.
- **Optional dependencies.** Vulnerabilities in `openai`/`anthropic` should be
  reported upstream; tell us only if textscope's use of them makes the impact
  worse.
