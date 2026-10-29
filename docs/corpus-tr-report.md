# Turkish academic corpus scan — findings and fixes

A 264-paragraph Turkish academic corpus was generated, rewritten by
`textscope`, and inspected for grammatical damage, meaning drift, formatting
artifacts, structural changes, protected-span changes and non-idempotency. Every
finding was attributed to the rule that produced it. Rules that repeatedly
damaged text were removed from `src/textscope/rules_tr.py` or replaced with an
idiomatic equivalent, and the scan was re-run until every hard category read
zero.

---

## 1. The corpus

`tests/corpus_tr_academic.py` builds `SAMPLES: list[str]` and
`SAMPLE_META: list[dict]` deterministically (no randomness at import time, no
`random` at all). Paragraphs are 4–6 sentences (mean 5.05, mean 58 words) and
are assembled from complete sentence frames whose slots are noun phrases that
already carry the case suffix the frame requires, so every sample is
grammatical by construction.

| Property | Value |
| --- | --- |
| Samples | 264 |
| Registers | 12 (22 each) |
| Domains | 10 |
| Styles | heavy nominalisation 96, plain prose 96, mixed 72 |
| Samples with number / % / year / citation / `\cite{}` / URL / abbreviation | 72 |

### Registers (22 samples each)

`thesis_intro`, `literature_review`, `methodology`, `findings`, `discussion`,
`conclusion`, `limitations`, `abstract`, `ethics_statement`, `grant_proposal`,
`conference_abstract`, `peer_review`.

### Domains

| Domain | Samples | Domain | Samples |
| --- | --- | --- | --- |
| health_sciences | 28 | psychology | 26 |
| education | 27 | computer_science | 26 |
| engineering | 27 | environmental_science | 26 |
| economics | 26 | law | 26 |
| sociology | 26 | business | 26 |

### Protected constructs

72 samples carry one of: a percentage plus a year (`%63`, `2019`), an
author-year citation (`(Yılmaz, 2019; Demir vd., 2021)`), a LaTeX citation
(`\cite{kaya2021,ozturk2020}`), a URL with `bkz.`/`ss.` abbreviations, or an
`2018-2022` range with `vb.`. Ethics statements and peer-review comments only
receive the citation/URL/abbreviation formats, so no ethics statement claims to
have improved its own participants.

---

## 2. How the scan works

`tests/test_corpus_tr.py` exposes `scan(samples) -> list[Issue]`; `Issue`
records the sample index, the attributed rule, the category, and the before /
after excerpt. Categories: `grammar_broken`, `meaning_shift`, `artifact`,
`structure_changed`, `protected_changed`, `not_changed`, `idempotent_violation`.

Implemented checks:

* **grammar_broken** — broken light-verb constructions (`inceleme edilmesini`),
  a finite verb followed by a light verb, impossible suffix stacking, a dative
  noun before the nominative postposition `hakkında`, a broken `hem … hem de`
  pair, and sentences with no finite verb and no nominal predicate.
* **artifact** — double spaces, space before punctuation, doubled words, doubled
  punctuation, glued words (`birbu`), a sentence starting lowercase (skipping
  abbreviation tails like `vb.`), a sentence ending in a dangling conjunction,
  and a sentence ending in a comma.
* **meaning_shift** (informational) — a diff-attributed check that a term of art
  or a content-bearing adverbial present in the source is absent from the output
  (`sürdürülebilir`, `analiz`, `doğrultusunda`, `son yıllarda`, `öncelikle`, …),
  plus negation and statistical-hedge counting.
* **structure_changed** — newline and paragraph counts.
* **protected_changed** — `textscope.protected.verify_protected` on every sample.
* **idempotent_violation** — a second rewrite pass must be a no-op.
* **not_changed** (informational) — the rewrite produced no change at all.

Issues are de-duplicated per `(sample, category, rule)` so a count means "this
rule damaged N samples", not "N punctuation marks". Rule attribution runs
through a word-level diff of source and output, plus the phrase pattern whose
match encloses the changed position.

---

## 3. Before the fixes (original `HEAD` rule table)

| Category | Count |
| --- | --- |
| grammar_broken | 96 |
| meaning_shift (informational) | 130 |
| idempotent_violation | 17 |
| artifact | 0 |
| structure_changed | 0 |
| protected_changed | 0 |

### Top 15 rule problems

| # | Rule | Count | Category | Before → After |
| --- | --- | --- | --- | --- |
| 1 | `hem de` → `ayrıca` (phrase) | 52 | grammar_broken | "hem uygulamada **hem de** hukuk alanında" → "hem uygulamada **ayrıca** hukuk alanında" |
| 2 | `ilişkin` → `hakkında` | 44 | grammar_broken | "işletmelere **ilişkin** beklentiler" → "işletmelere **hakkında** beklentiler" |
| 3 | `doğrultusunda` → `yönünde` | 44 | meaning_shift | "görüşleri **doğrultusunda** biçimlendirilmesi" → "görüşleri **yönünde** biçimlendirilmesi" |
| 4 | `son yıllarda` (leading-transition strip) | 22 | meaning_shift | "**Son yıllarda** uzaktan eğitim uygulamaları …" → "Uzaktan eğitim uygulamaları …" |
| 5 | `öncelikle` (leading-transition strip) | 17 | meaning_shift | "**Öncelikle** veriler … toplanmıştır." → "Veriler … toplandı." |
| 6 | `araştırma` → `çalışma` (second pass) | 17 | idempotent_violation | pass 1: "Araştırma kapsamında" → "**Çalışma** kapsamında"; pass 2: → "**Bu çalışmada**" |
| 7 | `sürdürülebilir` → `kalıcı` / `uzun ömürlü` | 13 | meaning_shift | "**sürdürülebilir** bir çerçevede" → "**uzun ömürlü** bir çerçevede" |
| 8 | `veri analizi` → `veri incelemesi` (+ 9 rules) | 13 | meaning_shift | "**panel veri analizi** ile ulaşılan" → "**panel veri incelemesi** ile ulaşılan" |
| 9 | `değerlendirme` → `ölçme` (+ 4 inflected rules) | 10 | meaning_shift | "deneysel **değerlendirme** kullanılarak" → "deneysel **ölçme** kullanılarak" |
| 10 | `değerlendirilmesi` → `ölçülmesi` | 5 | meaning_shift | "yeniden **değerlendirilmesi** gerektiğine" → "yeniden **ölçülmesi** gerektiğine" |
| 11 | `farklılık` → `ayrım` | 6 | meaning_shift | "gözlenen **farklılık**" → "gözlenen **ayrım**" |
| 12 | `belirgin` → `açık` | 42 word hits | meaning_shift | "**belirgin** bir iyileşme" → "**açık** bir iyileşme" ("openly") |
| 13 | `sistematik` → `düzenli` | 22 | meaning_shift | "**sistematik** biçimde kaydedilmesi" → "**düzenli** biçimde kaydedilmesi" |
| 14 | `yaygın olarak kabul edilmektedir` (shadowed) | 4 | meaning_shift | "**Yaygın olarak kabul edilmektedir**" → "**Geniş olarak kabul ediliyor**" |
| 15 | `ilk/ikinci/üçüncü/son olarak` strip | 22 | meaning_shift | "**Üçüncü olarak** … sonuçlar" → "… sonuçlar" (enumeration lost) |

Rows 12–15 were found by diffing all 134 distinct rewrites by hand and then
encoded as scan markers; they are reported at word-hit counts rather than
sample counts because several fire more than once per paragraph.

The corpus produced **no** `artifact`, `structure_changed` or
`protected_changed` findings against the original table — those categories are
implemented and asserted, but this corpus did not exercise them. The earlier
sentence-splitter and casing defects they target are covered by
`tests/test_quality_gate.py`.

---

## 4. What was changed and why

All changes are in `src/textscope/rules_tr.py`.

### Broken grammar (removed)

| Rule | Why |
| --- | --- |
| `(r"\bhem de\b", "ayrıca")` | `hem … hem de` is a correlative pair; replacing the second half leaves `hem … ayrıca`, which is ungrammatical in 52 samples. |
| `("ilişkin", "hakkında")` | `ilişkin` takes a dative and is postpositional; `hakkında` takes a bare nominative. "işletmelere hakkında" is impossible Turkish. |

### Non-idempotency (removed)

| Rule | Why |
| --- | --- |
| `("araştırma", "çalışma")` | Hop 1 turned `Araştırma kapsamında` into `Çalışma kapsamında`, which the phrase rule `çalışma kapsamında → bu çalışmada` then rewrote on the second pass. Root cause of all 17 idempotency violations, and also a meaning shift (`araştırma` = research, `çalışma` = study). |

### Terms of art replaced by near-synonyms (removed)

| Rules | Why |
| --- | --- |
| `sürdürülebilir → kalıcı`, `sürdürülebilirlik → kalıcılık`, `sürdürülebilirliği → kalıcılığı`, variant `sürdürülebilir` | Sustainability is not permanence; "uzun ömürlü bir çerçeve" is a different claim. |
| `değerlendirme → ölçme`, `değerlendirmek → ölçmek`, `değerlendirilmesi → ölçülmesi`, `değerlendirilmesinde → ölçülmesinde`, `değerlendirildiğinde → ölçüldüğünde` | Evaluation is not measurement; the family also produced the ungrammatical "ölçüme alındı". |
| `farklılık → ayrım` | A statistical difference is not a conceptual distinction. |
| `analiz sonuçları`, `veri analizi`, `verilerin analizi`, `veri analizleri`, `veri analizinde`, `verilerin analizinde`, `nicel analiz`, `nitel analiz`, `içerik analizi`, `doküman analizi` | These are method names. "içerik analizi" (content analysis) and "panel veri analizi" (panel data analysis) are fixed terms; "içerik incelemesi" is not the method. Verb uses (`analiz edilmektedir → incelenmektedir`) were kept. |
| `sağlamak → sunmak` | To ensure/provide is not to present: "Sağlamak istediğimiz temel hedef" became "Sunmak istediğimiz temel hedef". |
| `vizyon → bakış`, `misyon → amaç` | "Vizyon ve misyon belgeleri" are named institutional documents. |
| `ilişki → bağ`, `ilişkiler → bağlar` (and variant `ilişki`) | "Değişkenler arasındaki bağ anlamlıdır" is not statistical Turkish. |
| `süreç → akış`, `süreçler → akışlar` | Process is not flow in academic prose ("Süreç üç aşamada yürütülmüştür"). |
| `kapasite → hacim` | Capacity is not volume (engineering and economics). |
| `boyut → yön`, `boyutlar → yönler` | Dimension is not direction. |
| `evren → kitle` | In methodology `evren` is the population and `kitle` is a mass; "Evren ve örneklem" is a standard heading. |
| `yaygın → geniş` (and variant) | "Geniş olarak kabul ediliyor" is unidiomatic; `yaygın` is widespread, not wide. |
| `doğrultusunda → yönünde` | "In accordance with" became "toward". There is no single-word substitute that keeps the possessive+case the postposition needs, so it was removed rather than patched. |
| `("yanıstmak", "göstermek")` | Misspelled key (`yansıtmak`), so it never matched real text, and the mapping is a meaning change. |

### Content deletion (removed from `LEADING_TRANSITIONS_TR`)

`son yıllarda`, `son dönemde`, `şimdilerde`, `yakın zamanda`, `başlangıçta`,
`bu sırada`, `bu arada`, `bu esnada`, `aynı zamanda`, `ilk bakışta`,
`kısa vadede`, `öncelikle`, `ilk olarak`, `ikinci olarak`, `üçüncü olarak`,
`son olarak`.

These carry a timeframe or an enumeration order. Stripping them removed the time
frame of the study ("Son yıllarda …") or left an enumeration with a missing
member. Purely connective transitions (`ayrıca`, `öte yandan`, `dolayısıyla`,
`kısaca`, …) were kept.

### Rules replaced instead of removed

| Old | New | Why |
| --- | --- | --- |
| `belirgin → açık` | `belirgin → net` | `açık` reads as "openly" in "açık bir iyileşme"; `net` keeps the intended sense. |
| `sistematik → düzenli` | `sistematik → sistemli` | `düzenli` is "orderly/tidy"; `sistemli` keeps the methodological sense. |
| `amaç doğrultusunda → amaç yönünde` | `→ amaca yönelik` | Idiomatic replacement for the compliance phrase. |
| `amaçlar doğrultusunda → amaçlar yönünde` | `→ amaçlara yönelik` | Same. |
| `hedef doğrultusunda → hedef yönünde` | `→ hedefe yönelik` | Same. |
| `(r"\bkabul edilmektedir\b", "kabul ediliyor")` | removed | This generic rule ran **before** `yaygın olarak kabul edilmektedir → yaygın kabul görüyor`, shadowing it and producing "geniş olarak kabul ediliyor". The `-mektedir → -yor` form machinery already handles the generic case, so the rule was redundant *and* harmful. |

### Table impact

| Table | Before | After |
| --- | --- | --- |
| `WORD_SWAPS_TR` | 558 | 531 |
| `PHRASE_SWAPS_TR` | 317 | 301 |
| `LEADING_TRANSITIONS_TR` | 120 | 104 |

`tests/test_rules_tr.py` was touched in two places only, both directly caused by
the removals: the `sürdürülebilir` spelling probe (the key no longer exists) and
the leading-transition minimum (110 → 100, with a comment explaining that what
remains is purely connective). No behavioural assertion was loosened.

---

## 5. After the fixes

```
$ .venv/bin/python -c "import sys; sys.path.insert(0,'tests'); \
    from corpus_tr_academic import SAMPLES; \
    from test_corpus_tr import scan, category_counts; \
    print(category_counts(scan(SAMPLES)))"
{'not_changed': 16}
```

| Category | Before | After |
| --- | --- | --- |
| grammar_broken | 96 | **0** |
| artifact | 0 | **0** |
| structure_changed | 0 | **0** |
| protected_changed | 0 | **0** |
| idempotent_violation | 17 | **0** |
| meaning_shift (informational) | 130 | **0** |
| not_changed (informational) | 0 | 16 |

The 16 `not_changed` samples are short plain-style paragraphs whose every word
is already outside the table; that is a coverage gap, not damage.

### Verification

```
$ .venv/bin/python -m pytest -q                      # 152 passed (full suite)
$ .venv/bin/python -m ruff check src tests           # All checks passed!
```

To reproduce the scan table:

```
cd textscope
.venv/bin/python -c "
import sys; sys.path.insert(0, 'tests')
from corpus_tr_academic import SAMPLES
from test_corpus_tr import scan, category_counts, group_issues
issues = scan(SAMPLES)
print(category_counts(issues))
for category in ('grammar_broken', 'artifact', 'structure_changed',
                 'protected_changed', 'idempotent_violation'):
    print(category, group_issues(issues, category))
"
```

`tests/test_corpus_tr.py::test_scan_has_no_damaging_issues` enforces zero in the
five hard categories, so a regression fails the suite.

---

## 6. Remaining risks (not automatable)

1. **Causal and contrastive connectives are still deleted at sentence start.**
   `Dolayısıyla`, `Bu nedenle`, `Bununla birlikte`, `Ayrıca`, `Yani` and friends
   are in `LEADING_TRANSITIONS_TR`. Removing `Dolayısıyla` from "Dolayısıyla
   ortaya çıkan tablo …" drops an inference marker; the sentence stays
   grammatical, but the argument loses its connective. This is the tool's
   designed stylistic effect, so it was left alone — a human must judge whether
   the deleted link was load-bearing in a specific paragraph.
2. **Register lowering in formal text.** `gerekli → lazım`, `Bununla birlikte →
   Ama`, `dolayısıyla → bu yüzden` are grammatical but colloquial. In an ethics
   statement or a grant proposal this reads as a tone break rather than a
   wording change. No grammar heuristic can catch it.
3. **Mild synonym drift that survives.** `çerçevesinde → kapsamında`,
   `bağlamda → konuda`, `yetersiz → eksik`, `betimleyici → tanımlayıcı`,
   `disiplinler arası → çok alanlı`, `gösterge → işaret`, `unsur → öğe`,
   `bileşen → parça`. Each is defensible in some sentences and wrong in others
   ("betimleyici araştırma" is itself a standard term, so the swap is a lateral
   move). Only a reader who knows the specific sub-field can separate them.
4. **Quantitative nuance.** `büyük ölçüde → büyük oranda` and
   `önemli ölçüde → büyük oranda` collapse two different magnitudes into one.
   Same for `istatistiksel olarak anlamlı → anlamlı`, which drops the
   qualifier that distinguishes statistical from practical significance. The
   phrase table still contains the latter; it did not fire on this corpus.
5. **Sentence splitting.** The splitter is guarded by clause-starter and
   dangling-tail lists, but a legal or philosophical sentence whose subordinate
   clause opens with a word from `_CLAUSE_STARTERS_TR` can still be cut in a way
   that changes emphasis. The corpus produced no such case; adversarial legal
   prose is the place to look.
6. **Idempotency across profiles.** The scan uses the default balanced profile.
   `profile="aggressive"` merges `EXTRA_WORD_SWAPS_TR` after `_break_chains`, so
   chains can reappear in that mode; it was not exercised here and deserves its
   own scan.
7. **Coverage, not correctness.** 16 samples were left untouched and 531 word
   rules exist; the corpus exercises roughly 90 distinct swaps. Rules that never
   fire on this corpus (including several removed above, which were found by
   targeted probes) have not been validated against real prose.
