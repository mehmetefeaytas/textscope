"""Deterministic quality gate for textscope rewrites.

The rewriter claims to make AI-sounding prose read like human prose while
preserving meaning and protected zones. This module turns that claim into a
repeatable check: a fixed corpus of English and Turkish samples is rewritten
once, and every output is inspected for structural damage, over-deletion,
grammar artifacts, language drift, non-idempotency, and fragment sentences.

Standard library only. No network access, no random seeds beyond the
rewriter's own defaults.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .protected import split_protected, verify_protected
from .rewrite import detect_language, rewrite_text


@dataclass
class Sample:
    name: str
    text: str
    lang: str  # "en" | "tr"


EN_CORPUS: list[Sample] = [
    Sample(
        "en_ai_landscape",
        "In today's rapidly evolving digital landscape, it is important to note that "
        "artificial intelligence has fundamentally transformed the manner in which "
        "organizations approach data analysis. Moreover, the implementation of robust "
        "machine learning pipelines enables companies to leverage actionable insights "
        "in a seamless and efficient manner.\n\n"
        "The utilization of these technologies facilitates a comprehensive "
        "understanding of customer behavior, thereby allowing stakeholders to make "
        "informed decisions. Furthermore, it is worth mentioning that the integration "
        "of automation into existing workflows significantly enhances operational "
        "efficiency across the enterprise.",
        "en",
    ),
    Sample(
        "en_ai_education",
        "In recent years, there has been a growing recognition that digital tools play "
        "a crucial role in modern education. It is important to note that students who "
        "utilize interactive platforms demonstrate improved engagement and retention "
        "across a variety of subject areas.\n\n"
        "Educators should additionally consider the fact that access to reliable "
        "infrastructure constitutes a fundamental prerequisite for equitable learning. "
        "Consequently, institutions must endeavor to provide sufficient support for "
        "both teachers and learners.",
        "en",
    ),
    Sample(
        "en_ai_health",
        "It is worth noting that the healthcare sector has experienced a profound "
        "transformation as a result of technological innovation. Numerous studies have "
        "shown that early detection substantially improves patient outcomes and reduces "
        "the overall burden on clinical facilities.\n\n"
        "The deployment of predictive models additionally facilitates the efficient "
        "allocation of limited resources. Nevertheless, it should be emphasized that "
        "such systems require careful validation before they can be integrated into "
        "routine practice.",
        "en",
    ),
    Sample(
        "en_ai_business",
        "The contemporary business environment is characterized by an unprecedented "
        "degree of complexity and volatility. Organizations that fail to adapt their "
        "operational strategies to these changing conditions risk substantial losses in "
        "market share and long-term profitability.\n\n"
        "Consequently, it is essential that leadership teams establish clear priorities "
        "and communicate them effectively throughout the organization. Furthermore, "
        "investment in employee development constitutes a critical component of any "
        "sustainable growth strategy.",
        "en",
    ),
    Sample(
        "en_url_numbers",
        "Recent studies demonstrate that approximately 42% of respondents accessed the "
        "platform via https://example.com/survey/results during the initial observation "
        "period. The dataset, which comprises 1,250 records collected between 2019 and "
        "2023, provides a comprehensive overview of the observed trends.\n\n"
        "A follow-up analysis of 87 participants confirmed that the effect remained "
        "stable at 3.5 percentage points above the baseline described in the original "
        "report.",
        "en",
    ),
    Sample(
        "en_inline_code",
        "The implementation relies on the `transform_pipeline()` function, which "
        "processes each record and returns a normalized dictionary. It is important to "
        "note that the function must be invoked before the `finalize()` call in order to "
        "ensure consistency.\n\n"
        "Additionally, the `parse_config()` helper validates every entry in the input "
        "file before the pipeline begins. This approach prevents malformed records from "
        "propagating through subsequent stages of processing.",
        "en",
    ),
    Sample(
        "en_latex_cite",
        "Prior research has established a robust theoretical foundation for this "
        "phenomenon \\cite{smith2020,kaya2021}. Moreover, the findings presented in the "
        "literature suggest that the observed effects are consistent across multiple "
        "contexts.\n\n"
        "A related line of inquiry \\cite{lee2019} demonstrates that methodological "
        "choices substantially influence the reported magnitude of the effect. "
        "Therefore, future studies should endeavor to replicate these results using "
        "independent samples.",
        "en",
    ),
    Sample(
        "en_single_long_sentence",
        "In today's increasingly interconnected and rapidly evolving global landscape, "
        "it is critically important to recognize that the successful implementation of "
        "sustainable practices requires a comprehensive and multifaceted approach that "
        "simultaneously addresses economic, environmental, and social considerations "
        "while remaining adaptable to local conditions.",
        "en",
    ),
    Sample(
        "en_plain_baseline",
        "The sample was collected in March. The team measured the temperature twice "
        "each day. Approximately 40 readings were recorded at each site. The results "
        "were consistent across all three locations.",
        "en",
    ),
    Sample(
        "en_markdown_heading",
        "## Literature Review\n\n"
        "The existing body of research demonstrates that the relationship between the "
        "two variables is significant. Additionally, scholars have noted that the "
        "methodology employed in prior studies varies considerably.\n\n"
        "### Key Findings\n\n"
        "It is important to note that the majority of studies report a positive "
        "correlation. Moreover, the strength of this relationship appears to depend on "
        "the measurement instruments used.",
        "en",
    ),
    Sample(
        "en_ai_methodology",
        "This study utilizes a mixed-methods design in order to obtain a comprehensive "
        "understanding of the phenomenon under investigation. Data were collected from "
        "three distinct sources and subsequently analyzed using established statistical "
        "procedures.\n\n"
        "The sample consisted of 214 participants who were recruited through "
        "institutional mailing lists. Participation was voluntary, and all respondents "
        "provided informed consent prior to the commencement of the study.",
        "en",
    ),
    Sample(
        "en_ai_policy",
        "It is important to note that effective public policy requires a careful balance "
        "between innovation and regulation. Policymakers must therefore consider a wide "
        "range of perspectives when designing frameworks for emerging technologies.\n\n"
        "Furthermore, the absence of clear guidance may create uncertainty for "
        "organizations and discourage beneficial investment. Consequently, regulators "
        "should endeavor to establish transparent standards that are sufficiently "
        "flexible to accommodate future developments.",
        "en",
    ),
    Sample(
        "en_mixed_protected",
        "According to the latest report at https://data.example.org/2024/summary, "
        "approximately 68% of the 412 surveyed institutions have adopted the "
        "`ingest_batch()` routine \\cite{nguyen2023}. This finding is important because "
        "it suggests that adoption has accelerated since 2021.\n\n"
        "The authors note that the remaining 32% cited limited budgets as the primary "
        "obstacle. It is worth mentioning that follow-up interviews with 19 "
        "administrators confirmed this interpretation.",
        "en",
    ),
    Sample(
        "en_ai_conclusion",
        "In conclusion, the evidence presented in this paper suggests that technology "
        "adoption is a multifaceted process that cannot be reduced to a single factor. "
        "Future research should therefore examine the interaction between institutional "
        "context and individual behavior.\n\n"
        "It is also important to acknowledge the limitations of the present study. The "
        "sample was drawn from a single region, and the findings may not generalize to "
        "other settings.",
        "en",
    ),
]


TR_CORPUS: list[Sample] = [
    Sample(
        "tr_ai_dijital",
        "Günümüzün hızla değişen dijital dünyasında, yapay zekânın veri analizi "
        "süreçlerini temel biçimde dönüştürdüğünü belirtmek önemlidir. Ayrıca, sağlam "
        "makine öğrenmesi hatlarının uygulanması, şirketlerin eyleme dönüştürülebilir "
        "içgörüler elde etmesini kolaylaştırmaktadır.\n\n"
        "Bu teknolojilerin kullanımı, müşteri davranışının kapsamlı biçimde "
        "anlaşılmasını sağlamaktadır. Bunun yanı sıra, otomasyonun mevcut iş akışlarına "
        "entegre edilmesi kurumsal verimliliği önemli ölçüde artırmaktadır.",
        "tr",
    ),
    Sample(
        "tr_ai_egitim",
        "Son yıllarda dijital araçların çağdaş eğitimde önemli bir rol oynadığına dair "
        "giderek artan bir farkındalık bulunmaktadır. Etkileşimli platformları kullanan "
        "öğrencilerin çeşitli konu alanlarında daha yüksek katılım ve kalıcılık "
        "gösterdiğini belirtmek önemlidir.\n\n"
        "Eğitimciler ayrıca güvenilir altyapıya erişimin hakkaniyetli öğrenme için temel "
        "bir önkoşul oluşturduğu gerçeğini göz önünde bulundurmalıdır. Dolayısıyla "
        "kurumlar hem öğretmenler hem de öğrenciler için yeterli destek sağlamaya özen "
        "göstermelidir.",
        "tr",
    ),
    Sample(
        "tr_ai_saglik",
        "Sağlık sektörünün teknolojik yenilikler sonucunda köklü bir dönüşüm yaşadığını "
        "belirtmek gerekir. Çok sayıda çalışma, erken teşhisin hasta sonuçlarını önemli "
        "ölçüde iyileştirdiğini ve klinik tesisler üzerindeki genel yükü azalttığını "
        "göstermektedir.\n\n"
        "Kestirim modellerinin devreye alınması ayrıca sınırlı kaynakların verimli "
        "biçimde tahsis edilmesini kolaylaştırmaktadır. Bununla birlikte, bu tür "
        "sistemlerin rutin uygulamaya entegre edilmeden önce dikkatli biçimde "
        "doğrulanması gerektiği vurgulanmalıdır.",
        "tr",
    ),
    Sample(
        "tr_url_sayilar",
        "Son çalışmalar, katılımcıların yaklaşık %42'sinin ilk gözlem döneminde "
        "https://ornek.com/arastirma adresine eriştiğini göstermektedir. 2019 ile 2023 "
        "yılları arasında toplanan 1.250 kayıttan oluşan veri seti, gözlenen eğilimlerin "
        "kapsamlı bir görünümünü sunmaktadır.\n\n"
        "Seksen yedi katılımcıyla yapılan ek analiz, etkinin başlangıç değerinin 3,5 "
        "puan üzerinde kararlı kaldığını doğrulamaktadır.",
        "tr",
    ),
    Sample(
        "tr_satir_ici_kod",
        "Uygulama, her kaydı işleyen ve normalize edilmiş bir sözlük döndüren "
        "`donustur()` işlevine dayanmaktadır. Tutarlılığı sağlamak için işlevin "
        "`sonlandir()` çağrısından önce kullanılması gerekmektedir.\n\n"
        "Ayrıca `ayar_oku()` yardımcı işlevi, işlem hattı başlamadan önce girdi "
        "dosyasındaki her kaydı doğrulamaktadır. Bu yaklaşım bozuk kayıtların sonraki "
        "aşamalara yayılmasını engellemektedir.",
        "tr",
    ),
    Sample(
        "tr_latex_atif",
        "Önceki araştırmalar bu olgu için sağlam bir kuramsal temel oluşturmuştur "
        "\\cite{yilmaz2020,kaya2021}. Ayrıca literatürde sunulan bulgular, gözlenen "
        "etkilerin birden fazla bağlamda tutarlı olduğunu göstermektedir.\n\n"
        "İlgili bir çalışma \\cite{demir2019}, yöntemsel tercihlerin bildirilen etki "
        "büyüklüğünü önemli ölçüde etkilediğini ortaya koymaktadır. Bu nedenle gelecek "
        "çalışmaların bu sonuçları bağımsız örneklemlerle yinelemesi gerekmektedir.",
        "tr",
    ),
    Sample(
        "tr_tek_uzun_cumle",
        "Günümüzün giderek birbirine bağlanan ve hızla değişen küresel ortamında, "
        "sürdürülebilir uygulamaların başarılı biçimde hayata geçirilmesinin ekonomik, "
        "çevresel ve toplumsal boyutları aynı anda ele alan kapsamlı bir yaklaşım "
        "gerektirdiğini kabul etmek son derece önemlidir.",
        "tr",
    ),
    Sample(
        "tr_sade_taban",
        "Örnekler mart ayında toplandı. Ekip sıcaklığı her gün iki kez ölçtü. Her "
        "merkezde yaklaşık 40 okuma kaydedildi. Toplanan veriler sistematik biçimde "
        "dosyalandı. Sonuçlar üç merkezde de tutarlıydı.",
        "tr",
    ),
    Sample(
        "tr_markdown_baslik",
        "## Literatür Taraması\n\n"
        "Mevcut araştırma birikimi, iki değişken arasındaki ilişkinin anlamlı olduğunu "
        "göstermektedir. Ayrıca araştırmacılar, önceki çalışmalarda kullanılan yöntemin "
        "önemli ölçüde farklılaştığını belirtmektedir.\n\n"
        "### Temel Bulgular\n\n"
        "Çalışmaların çoğunun olumlu bir ilişki bildirdiğini belirtmek önemlidir. "
        "Üstelik bu ilişkinin gücü kullanılan ölçüm araçlarına bağlı görünmektedir.",
        "tr",
    ),
    Sample(
        "tr_yontem",
        "Bu çalışma, incelenen olguya ilişkin kapsamlı bir anlayış elde etmek amacıyla "
        "karma yöntemli bir tasarım kullanmaktadır. Veriler üç ayrı kaynaktan toplanmış "
        "ve ardından yerleşik istatistiksel yordamlar kullanılarak analiz edilmiştir.\n\n"
        "Örneklem, kurumsal e-posta listeleri aracılığıyla ulaşılan 214 katılımcıdan "
        "oluşmaktadır. Katılım gönüllülük esasına dayanmaktadır ve tüm katılımcılar "
        "çalışmanın başlangıcından önce bilgilendirilmiş onam vermiştir.",
        "tr",
    ),
    Sample(
        "tr_politika",
        "Etkili kamu politikasının yenilik ile düzenleme arasında dikkatli bir denge "
        "gerektirdiğini belirtmek önemlidir. Bu nedenle politika yapıcılar, gelişmekte "
        "olan teknolojilere yönelik çerçeveler tasarlarken çok çeşitli bakış açılarını "
        "göz önünde bulundurmalıdır.\n\n"
        "Ayrıca açık bir yönlendirmenin bulunmaması, kuruluşlar için belirsizlik "
        "yaratabilir ve faydalı yatırımları caydırabilir. Dolayısıyla düzenleyiciler, "
        "gelecekteki gelişmelere uyum sağlayacak kadar esnek ve şeffaf standartlar "
        "oluşturmaya özen göstermelidir.",
        "tr",
    ),
    Sample(
        "tr_karma_korunan",
        "https://veri.ornek.org/2024/ozet adresindeki son rapora göre, ankete katılan "
        "412 kurumun yaklaşık %68'i `toplu_aktar()` yordamını \\cite{nguyen2023} "
        "benimsemiştir. Bu bulgu önemlidir çünkü benimsemenin 2021 yılından bu yana "
        "hızlandığını göstermektedir.\n\n"
        "Yazarlar, geriye kalan %32'lik kesimin temel engel olarak sınırlı bütçeleri "
        "gösterdiğini belirtmektedir. On dokuz yöneticiyle yapılan görüşmelerin bu "
        "yorumu doğruladığını belirtmek gerekir.",
        "tr",
    ),
    Sample(
        "tr_sonuc",
        "Sonuç olarak, bu makalede sunulan kanıtlar teknoloji benimsemesinin tek bir "
        "etkene indirgenemeyecek kadar çok boyutlu bir süreç olduğunu göstermektedir. "
        "Bu nedenle gelecek araştırmalar kurumsal bağlam ile bireysel davranış "
        "arasındaki etkileşimi incelemelidir.\n\n"
        "Mevcut çalışmanın sınırlılıklarını da kabul etmek önemlidir. Örneklem tek bir "
        "bölgeden toplanmıştır ve bulgular başka ortamlara genellenemeyebilir.",
        "tr",
    ),
]


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")
_DOUBLE_SPACE = re.compile(r"  +")
_SPACE_BEFORE_PUNCT = re.compile(r"\s+[,.;:!?]")
_EMPTY_BRACKETS = re.compile(r"\(\s*\)|\[\s*\]")
_DOUBLED_WORD = re.compile(r"\b(\w+) \1\b", re.IGNORECASE)
_LOWER_AFTER_PERIOD = re.compile(r"[.!?][ \t]+[a-zçğıöşü]")
_TRAILING_CONJ_EN = re.compile(r"\b(and|but|or|of|to|in|for)\s*$", re.IGNORECASE)
_TRAILING_CONJ_TR = re.compile(r"\b(ve|ama|veya|ile|için)\s*$", re.IGNORECASE)
_BLANK_SEPARATOR = re.compile(r"\n[ \t]*\n")

_SHORT_SENTENCE_WORDS = 4


def _words(text: str) -> int:
    return len(text.split())


def _short_sentences(text: str) -> list[str]:
    """Sentences with fewer than four words, counted line by line."""
    found: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        for sentence in _SENT_SPLIT.split(stripped):
            sentence = sentence.strip()
            if sentence and _words(sentence) < _SHORT_SENTENCE_WORDS:
                found.append(sentence)
    return found


def _line_word_drops(source: str, rewritten: str) -> list[str]:
    """Lines (paired by position) that lost more than 40% of their words."""
    src_lines = source.splitlines()
    out_lines = rewritten.splitlines()
    if len(src_lines) != len(out_lines):
        return []
    problems: list[str] = []
    for idx, (src, out) in enumerate(zip(src_lines, out_lines), start=1):
        src_words = _words(src)
        if src_words < _SHORT_SENTENCE_WORDS:
            continue
        lost = (src_words - _words(out)) / src_words
        if lost > 0.40:
            problems.append(f"line {idx}: {src_words} -> {_words(out)} words ({lost:.0%} lost)")
    return problems


def _check_protected(sample: Sample, rewritten: str) -> CheckResult:
    ok, errors = verify_protected(sample.text, rewritten)
    detail = "protected spans identical" if ok else "; ".join(errors)
    return CheckResult("protected_ok", ok, detail)


def _check_structure(sample: Sample, rewritten: str) -> CheckResult:
    src_newlines = sample.text.count("\n")
    out_newlines = rewritten.count("\n")
    src_blanks = len(_BLANK_SEPARATOR.findall(sample.text))
    out_blanks = len(_BLANK_SEPARATOR.findall(rewritten))
    ok = src_newlines == out_newlines and src_blanks == out_blanks
    detail = (
        f"newlines {src_newlines}->{out_newlines}, "
        f"blank separators {src_blanks}->{out_blanks}"
    )
    return CheckResult("structure_ok", ok, detail)


def _check_word_budget(sample: Sample, rewritten: str) -> CheckResult:
    src_words = _words(sample.text)
    out_words = _words(rewritten)
    if src_words == 0:
        return CheckResult("word_budget", True, "empty source")
    total_delta = (out_words - src_words) / src_words
    problems: list[str] = []
    if abs(total_delta) > 0.20:
        problems.append(
            f"total words {src_words}->{out_words} ({total_delta:+.0%}, limit +/-20%)"
        )
    problems.extend(_line_word_drops(sample.text, rewritten))
    if problems:
        return CheckResult("word_budget", False, "; ".join(problems))
    return CheckResult(
        "word_budget", True, f"total words {src_words}->{out_words} ({total_delta:+.0%})"
    )


def _mask_protected(text: str) -> str:
    """Replace protected spans with a neutral token.

    Artifact checks must not inspect code, URLs, LaTeX or numbers: ``foo()``
    is a legitimate call, not an empty bracket pair. Masking also avoids
    creating phantom double spaces where a protected span was removed.
    """
    return "".join(
        "X" if span.protected else span.text for span in split_protected(text)
    )


def _check_artifacts(sample: Sample, rewritten: str) -> CheckResult:
    prose = _mask_protected(rewritten)
    problems: list[str] = []
    if _DOUBLE_SPACE.search(prose):
        problems.append("double space")
    if _SPACE_BEFORE_PUNCT.search(prose):
        problems.append("space before punctuation")
    if _EMPTY_BRACKETS.search(prose):
        problems.append("empty brackets")
    doubled = _DOUBLED_WORD.search(prose)
    if doubled:
        problems.append(f"doubled word: {doubled.group(0)!r}")
    lower = _LOWER_AFTER_PERIOD.search(prose)
    if lower:
        problems.append(f"lowercase after period: {lower.group(0).strip()!r}")
    conj = _TRAILING_CONJ_TR if sample.lang == "tr" else _TRAILING_CONJ_EN
    for idx, line in enumerate(prose.splitlines(), start=1):
        if conj.search(line):
            problems.append(f"line {idx} ends with conjunction: {line.strip()[-24:]!r}")
    if problems:
        return CheckResult("no_artifacts", False, "; ".join(problems))
    return CheckResult("no_artifacts", True, "no rewriting artifacts")


def _check_language(sample: Sample, rewritten: str) -> CheckResult:
    detected = detect_language(rewritten)
    ok = detected == sample.lang
    return CheckResult("language_kept", ok, f"detected {detected!r}, expected {sample.lang!r}")


def _check_idempotent(sample: Sample, rewritten: str) -> CheckResult:
    again = rewrite_text(rewritten, lang=sample.lang)
    if again == rewritten:
        return CheckResult("idempotent", True, "second pass is byte-identical")
    first_diff = next(
        (
            i
            for i, (a, b) in enumerate(zip(rewritten, again))
            if a != b
        ),
        min(len(rewritten), len(again)),
    )
    window_a = rewritten[max(0, first_diff - 30):first_diff + 30]
    window_b = again[max(0, first_diff - 30):first_diff + 30]
    return CheckResult(
        "idempotent",
        False,
        f"diff at char {first_diff}: {window_a!r} -> {window_b!r}",
    )


def _check_changed(sample: Sample, rewritten: str) -> CheckResult:
    ok = rewritten != sample.text
    detail = "output differs from source" if ok else "output is identical to source"
    return CheckResult("changed", ok, detail)


def _check_fragments(sample: Sample, rewritten: str) -> CheckResult:
    src_short = _short_sentences(sample.text)
    out_short = _short_sentences(rewritten)
    if len(out_short) <= len(src_short):
        return CheckResult(
            "no_fragment_sentences",
            True,
            f"short sentences {len(src_short)}->{len(out_short)}",
        )
    new_ones = [s for s in out_short if _normalize_sentence(s) not in _normalize_all(src_short)]
    detail = f"short sentences {len(src_short)}->{len(out_short)}"
    if new_ones:
        detail += "; new: " + ", ".join(repr(s) for s in new_ones[:3])
    return CheckResult("no_fragment_sentences", False, detail)


def _normalize_sentence(sentence: str) -> str:
    return re.sub(r"\s+", " ", sentence.strip().lower())


def _normalize_all(sentences: list[str]) -> set[str]:
    return {_normalize_sentence(s) for s in sentences}


# ---------------------------------------------------------------------------
# public API
# ---------------------------------------------------------------------------

CHECK_ORDER = (
    "protected_ok",
    "structure_ok",
    "word_budget",
    "no_artifacts",
    "language_kept",
    "idempotent",
    "changed",
    "no_fragment_sentences",
)


def run_checks(sample: Sample, rewritten: str) -> list[CheckResult]:
    """Run every quality check against one rewrite."""
    return [
        _check_protected(sample, rewritten),
        _check_structure(sample, rewritten),
        _check_word_budget(sample, rewritten),
        _check_artifacts(sample, rewritten),
        _check_language(sample, rewritten),
        _check_idempotent(sample, rewritten),
        _check_changed(sample, rewritten),
        _check_fragments(sample, rewritten),
    ]


def default_corpus() -> list[Sample]:
    return [*EN_CORPUS, *TR_CORPUS]


def evaluate(corpus: list[Sample] | None = None) -> dict:
    """Rewrite every sample and aggregate check results."""
    samples = default_corpus() if corpus is None else list(corpus)
    results: list[dict] = []
    check_counts: dict[str, dict[str, int]] = {
        name: {"passed": 0, "total": 0} for name in CHECK_ORDER
    }
    total_passed = 0
    total_checks = 0

    for sample in samples:
        rewritten = rewrite_text(sample.text, lang=sample.lang)
        checks = run_checks(sample, rewritten)
        failed = [c for c in checks if not c.passed]
        for check in checks:
            bucket = check_counts.setdefault(check.name, {"passed": 0, "total": 0})
            bucket["total"] += 1
            if check.passed:
                bucket["passed"] += 1
        total_checks += len(checks)
        total_passed += len(checks) - len(failed)
        results.append(
            {
                "name": sample.name,
                "lang": sample.lang,
                "passed": not failed,
                "checks": checks,
                "rewritten": rewritten,
                "failed": [c.name for c in failed],
            }
        )

    per_lang: dict[str, dict[str, int]] = {}
    for sample, row in zip(samples, results):
        bucket = per_lang.setdefault(sample.lang, {"samples": 0, "passed": 0})
        bucket["samples"] += 1
        if row["passed"]:
            bucket["passed"] += 1

    return {
        "samples": results,
        "check_counts": check_counts,
        "per_lang": per_lang,
        "total": {
            "samples": len(samples),
            "samples_passed": sum(1 for r in results if r["passed"]),
            "checks": total_checks,
            "checks_passed": total_passed,
            "pass_rate": total_passed / total_checks if total_checks else 1.0,
        },
    }


def _status(passed: bool) -> str:
    return "PASS" if passed else "FAIL"


def format_report(result: dict) -> str:
    """Render an evaluate() result as a plain-text table."""
    lines: list[str] = []
    total = result["total"]
    lines.append("textscope quality gate")
    lines.append("=" * 62)
    lines.append(
        f"samples: {total['samples_passed']}/{total['samples']} clean    "
        f"checks: {total['checks_passed']}/{total['checks']} passed "
        f"({total['pass_rate']:.1%})"
    )
    lines.append("")
    lines.append(f"{'sample':<28} {'lang':<5} {'status':<7} failing checks")
    lines.append("-" * 62)
    for row in result["samples"]:
        failing = ", ".join(row["failed"]) if row["failed"] else "-"
        lines.append(
            f"{row['name']:<28} {row['lang']:<5} {_status(row['passed']):<7} {failing}"
        )
    lines.append("")
    lines.append(f"{'check':<28} {'passed':>7} {'total':>6}  rate")
    lines.append("-" * 62)
    for name in CHECK_ORDER:
        bucket = result["check_counts"].get(name, {"passed": 0, "total": 0})
        rate = bucket["passed"] / bucket["total"] if bucket["total"] else 1.0
        lines.append(
            f"{name:<28} {bucket['passed']:>7} {bucket['total']:>6}  {rate:.0%}"
        )
    lines.append("")
    for lang in sorted(result.get("per_lang", {})):
        bucket = result["per_lang"][lang]
        lines.append(f"{lang}: {bucket['passed']}/{bucket['samples']} samples clean")
    return "\n".join(lines)
