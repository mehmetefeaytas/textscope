"""Tests for the expanded English/Turkish rule sets."""

from textscope.protected import verify_protected
from textscope.rewrite import (
    _apply_turkish_forms,
    _upper_first,
    detect_language,
    rewrite_text,
)

# ---------- language detection ----------

def test_detect_turkish_with_special_letters():
    assert detect_language("Bu çalışmada geniş bir analiz yapıldı.") == "tr"


def test_detect_ascii_only_turkish():
    assert detect_language("Bu calisma kapsaminda genis bir analiz yapilmistir.") == "tr"


def test_detect_english():
    assert detect_language("The report is at the office and it is ready.") == "en"
    assert detect_language("Moreover, the data show a robust trend.") == "en"


# ---------- Turkish verb forms ----------

def test_turkish_progressive_softening():
    out = _apply_turkish_forms("Sonuçlar göstermektedir ve veriler sağlanmaktadır.")
    assert "gösteriyor" in out
    assert "sağlanıyor" in out
    assert "mektedir" not in out
    assert "maktadır" not in out


def test_turkish_progressive_vowel_stems():
    out = _apply_turkish_forms("Öğrenci okumaktadır ve öğretmen beklemektedir.")
    assert "okuyor" in out
    assert "bekliyor" in out


def test_turkish_progressive_softens_t_stems():
    assert _apply_turkish_forms("Bu ifade etmektedir.") == "Bu ifade ediyor."
    assert _apply_turkish_forms("Araç gitmektedir.") == "Araç gidiyor."


def test_turkish_progressive_plural():
    assert _apply_turkish_forms("Öğrenciler gelmektedirler.") == "Öğrenciler geliyorlar."


def test_turkish_simple_past():
    assert _apply_turkish_forms("Bu konu incelenmiştir.") == "Bu konu incelendi."
    assert _apply_turkish_forms("Çalışma yapılmıştır.") == "Çalışma yapıldı."
    assert _apply_turkish_forms("O etmiştir.") == "O etti."
    assert _apply_turkish_forms("Veriler toplanmıştır.") == "Veriler toplandı."


def test_turkish_future_and_necessity():
    assert _apply_turkish_forms("Sonuç olacaktır.") == "Sonuç olacak."
    assert _apply_turkish_forms("Analiz yapılmalıdır.") == "Analiz yapılmalı."


def test_turkish_verb_forms_preserve_word_count():
    text = "Veriler incelenmiştir ve sonuçlar göstermektedir."
    assert len(_apply_turkish_forms(text).split()) == len(text.split())


def test_turkish_capital_i():
    assert _upper_first("işlev", "tr") == "İşlev"
    assert _upper_first("ılık", "tr") == "Ilık"
    assert _upper_first("işlev", "en") == "Işlev"


def test_turkish_rewrite_keeps_protected_zones():
    text = "Araştırma 42 katılımcı ile https://example.com üzerinden yapılmıştır."
    out = rewrite_text(text, lang="tr")
    assert "42" in out
    assert "https://example.com" in out
    ok, errors = verify_protected(text, out)
    assert ok, errors


def test_turkish_output_is_readable():
    text = (
        "Bu çalışmada kapsamlı bir literatür taraması gerçekleştirilmiştir. "
        "Bulgular, yöntemin öğrenciler üzerinde önemli bir rol oynadığını göstermektedir. "
        "Ayrıca verilerin daha etkin analiz edilmesini sağlamaktadır."
    )
    out = rewrite_text(text, lang="tr")
    assert "mektedir" not in out
    assert "maktadır" not in out
    assert "gerçekleştirilmiştir" not in out
    assert ".dı" not in out  # regression: truncated "Adı"
    assert "  " not in out


# ---------- English expansion ----------

def test_english_expanded_word_swaps():
    out = rewrite_text("This demonstrates how we obtain numerous benefits.")
    assert "shows" in out
    assert "get" in out
    assert "numerous" not in out


def test_english_expanded_phrase_swaps():
    out = rewrite_text("In order to finish, we take into account the data.")
    assert "In order to" not in out
    assert "consider" in out


def test_english_contraction_set():
    out = rewrite_text("They will not finish. There is no time.")
    assert "won't" in out
    assert "There's" in out


def test_english_humanizer_keeps_meaning_markers():
    out = rewrite_text("The sample was 42 units and the URL https://x.com/a remained.")
    assert "42" in out
    assert "https://x.com/a" in out


# ---------- strict mode ----------

def test_strict_filters_multiword_swaps_but_still_rewrites():
    text = "Moreover, this comprehensive study utilizes robust methods."
    out = rewrite_text(text, strict=True)
    assert len(out.split()) == len(text.split())
    assert out != text


def test_strict_turkish_still_softens_verbs():
    text = "Sonuçlar göstermektedir ve veriler incelenmiştir."
    out = rewrite_text(text, lang="tr", strict=True)
    assert len(out.split()) == len(text.split())
    assert "gösteriyor" in out
    assert "incelendi" in out
