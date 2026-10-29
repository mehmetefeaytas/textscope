from __future__ import annotations

import re

from .protected import Span, reassemble, split_protected

# ---------- English rules ----------

WORD_SWAPS_EN = {
    "delve": "explore", "delving": "exploring", "tapestry": "mix",
    "multifaceted": "complex", "nuanced": "subtle", "pivotal": "key",
    "crucial": "important", "vital": "essential", "paramount": "top",
    "underscore": "highlight", "foster": "build", "bolster": "boost",
    "leverage": "use", "utilize": "use", "utilizes": "uses",
    "utilized": "used", "utilizing": "using", "facilitate": "help",
    "streamline": "simplify", "robust": "strong", "comprehensive": "full",
    "meticulous": "careful", "seamless": "smooth", "groundbreaking": "new",
    "transformative": "big", "paradigm": "model", "synergy": "teamwork",
    "holistic": "whole", "ecosystem": "system", "landscape": "field",
    "realm": "area", "plethora": "many", "myriad": "many", "embark": "start",
    "navigate": "handle", "harness": "use", "spearhead": "lead",
    "champion": "support", "elevate": "raise", "empower": "enable",
    "unlock": "open", "unleash": "release", "revolutionize": "change",
    "optimize": "improve", "furthermore": "also", "moreover": "also",
    "additionally": "also", "consequently": "so", "therefore": "so",
    "nevertheless": "still", "nonetheless": "still", "ultimately": "finally",
    "significantly": "notably", "notably": "notably", "importantly": "key",
    "interestingly": "oddly", "surprisingly": "surprisingly",
}

PHRASE_SWAPS_EN = [
    (r"\bit is important to note that\b", "note that"),
    (r"\bit is worth noting that\b", "note that"),
    (r"\bit should be noted that\b", "note that"),
    (r"\bit is worth mentioning that\b", "note that"),
    (r"\bplays a crucial role in\b", "matters for"),
    (r"\bplays a vital role in\b", "matters for"),
    (r"\bplays a key role in\b", "matters for"),
    (r"\bserves as a\b", "is a"), (r"\bserves as an\b", "is an"),
    (r"\ba wide range of\b", "many"), (r"\ba variety of\b", "various"),
    (r"\bin order to\b", "to"), (r"\bdue to the fact that\b", "because"),
    (r"\bin spite of the fact that\b", "although"),
    (r"\bat this point in time\b", "now"), (r"\bin the event that\b", "if"),
    (r"\bfor the purpose of\b", "to"), (r"\bwith regard to\b", "about"),
    (r"\bin terms of\b", "in"), (r"\bon the basis of\b", "based on"),
    (r"\bas a matter of fact\b", "in fact"),
    (r"\bin light of the fact that\b", "since"),
    (r"\bwith respect to\b", "about"), (r"\bin the context of\b", "in"),
    (r"\bat the end of the day\b", "ultimately"),
    (r"\bfirst and foremost\b", "first"),
]

LEADING_TRANSITIONS_EN = [
    "moreover", "furthermore", "additionally", "in addition",
    "consequently", "therefore", "thus", "hence", "nevertheless",
    "nonetheless", "however", "meanwhile", "in conclusion", "to conclude",
    "in summary", "to summarize", "in essence", "ultimately", "overall",
    "importantly", "notably", "significantly", "interestingly",
    "surprisingly", "on the other hand", "on the contrary",
]

CONTRACTIONS_EN = [
    (r"\bdo not\b", "don't"), (r"\bcannot\b", "can't"), (r"\bcan not\b", "can't"),
    (r"\bit is\b", "it's"), (r"\bthat is\b", "that's"), (r"\bwe are\b", "we're"),
    (r"\bthey are\b", "they're"), (r"\byou are\b", "you're"), (r"\bi am\b", "I'm"),
    (r"\bwill not\b", "won't"), (r"\bis not\b", "isn't"), (r"\bare not\b", "aren't"),
    (r"\bwas not\b", "wasn't"), (r"\bwere not\b", "weren't"),
    (r"\bhas not\b", "hasn't"), (r"\bhave not\b", "haven't"),
    (r"\bhad not\b", "hadn't"), (r"\bdoes not\b", "doesn't"),
    (r"\bdid not\b", "didn't"), (r"\blet us\b", "let's"),
]

# ---------- Turkish rules ----------

WORD_SWAPS_TR = {
    "kapsamlı": "geniş", "etkin": "etkili", "verimli": "faydalı",
    "sürdürülebilir": "kalıcı", "bütüncül": "bütün", "kayda değer": "önemli",
    "dikkat çekici": "ilginç", "optimum": "en iyi", "maksimize": "artır",
    "minimize": "azalt", "stratejik": "planlı", "proaktif": "önceden",
    "sinergi": "işbirliği", "paradigma": "yaklaşım", "dinamik": "hareketli",
    "holistik": "bütüncül", "ekosistem": "sistem", "multidisipliner": "çok alanlı",
    "inovatif": "yenilikçi", "robust": "güçlü", "kapsayıcı": "kapsayıcı",
    "optimize": "geliştir", "facilitate": "kolaylaştır",
}

PHRASE_SWAPS_TR = [
    (r"\bbelirtmek gerekir ki\b", "belirtelim,"),
    (r"\bifade etmek gerekir\b", "belirtelim"),
    (r"\bvurgulamak gerekir\b", "vurgulayalım"),
    (r"\bunutulmamalıdır ki\b", "unutmayın"),
    (r"\bbilinmelidir ki\b", "bilinmeli"),
    (r"\baçıkça görülmektedir\b", "açıkça görülüyor"),
    (r"\belde edilen bulgular\b", "bulgular"),
    (r"\bsonuçlar göstermektedir\b", "sonuçlar gösteriyor"),
    (r"\bliteratürde\b", "yazında"),
    (r"\bçalışma kapsamında\b", "bu çalışmada"),
    (r"\baraştırma sonuçları\b", "sonuçlar"),
    (r"\bönerilmektedir\b", "öneriliyor"),
    (r"\bdeğerlendirilmektedir\b", "değerlendiriliyor"),
    (r"\boptimize edebiliriz\b", "geliştirebiliriz"),
    (r"\boptimize edebilir\b", "geliştirebilir"),
    (r"\bonemli bir rol oynamaktadır\b", "önemli"),
    (r"\bbu bağlamda\b", "bu konuda"),
    (r"\bbu noktada\b", "burada"),
    (r"\bbuna ek olarak\b", "ayrıca"),
    (r"\bbununla birlikte\b", "ama"),
    (r"\bdiğer yandan\b", "öte yandan"),
    (r"\bgenel olarak\b", "genelde"),
    (r"\bbir başka deyişle\b", "yani"),
    (r"\bsonuç olarak\b", "sonuçta"),
    (r"\bözetle\b", "kısaca"),
]

LEADING_TRANSITIONS_TR = [
    "sonuç olarak", "bu bağlamda", "bu noktada", "ayrıca", "bununla birlikte",
    "buna ek olarak", "diğer yandan", "öte yandan", "özetle", "genel olarak",
    "bir başka deyişle", "dolayısıyla", "bu nedenle", "bu sebeple",
    "buna göre", "bu durumda", "bu çerçevede", "bu kapsamda",
]

CONTRACTIONS_TR = []  # Turkish doesn't use contractions similarly


def detect_language(text: str) -> str:
    tr_chars = set("çğıöşüÇĞİÖŞÜ")
    count = sum(1 for ch in text if ch in tr_chars)
    if count >= 3:
        return "tr"
    # common Turkish words
    low = text.lower()
    tr_words = ["bir", "ve", "için", "ile", "bu", "şu", "olan", "olarak", "gibi", "daha", "kadar"]
    hits = sum(1 for w in tr_words if f" {w} " in f" {low} ")
    if hits >= 4:
        return "tr"
    return "en"


def _rules(lang: str):
    if lang == "tr":
        return (WORD_SWAPS_TR, PHRASE_SWAPS_TR, LEADING_TRANSITIONS_TR, CONTRACTIONS_TR)
    return (WORD_SWAPS_EN, PHRASE_SWAPS_EN, LEADING_TRANSITIONS_EN, CONTRACTIONS_EN)


def _preserve_case(original: str, replacement: str) -> str:
    if original and original[0].isupper():
        return replacement[0].upper() + replacement[1:] if replacement else replacement
    return replacement


def _apply_word_swaps(text: str, swaps: dict) -> str:
    if not swaps:
        return text
    pattern = r"\b(" + "|".join(re.escape(k) for k in sorted(swaps, key=len, reverse=True)) + r")\b"
    def repl(m):
        w = m.group(0)
        low = w.lower()
        if low in swaps:
            return _preserve_case(w, swaps[low])
        return w
    return re.sub(pattern, repl, text, flags=re.IGNORECASE)


def _apply_phrase_swaps(text: str, swaps: list) -> str:
    for pat, rep in swaps:
        def repl(m, rep=rep):
            return _preserve_case(m.group(0), rep)
        text = re.sub(pat, repl, text, flags=re.IGNORECASE)
    return text


def _remove_leading_transitions(text: str, transitions: list) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    out = []
    for s in sentences:
        s2 = s
        for tr in transitions:
            m = re.match(r"(\s*)" + re.escape(tr) + r"\b\s*,?\s*", s2, flags=re.IGNORECASE)
            if m:
                lead = m.group(1)
                rest = s2[m.end():]
                if rest.strip():
                    s2 = lead + rest
                    stripped = s2.lstrip()
                    if stripped and stripped[0].islower():
                        idx = len(s2) - len(stripped)
                        s2 = s2[:idx] + stripped[0].upper() + stripped[1:]
                break
        out.append(s2)
    return " ".join(out)


def _apply_contractions(text: str, contractions: list) -> str:
    for pat, rep in contractions:
        text = re.sub(pat, rep, text, flags=re.IGNORECASE)
    return text


def _split_long_sentences(text: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    out = []
    for s in sentences:
        words = s.split()
        if len(words) > 10:
            ci = s.find(",")
            if ci > 8 and ci < len(s) - 5:
                left = s[:ci] + "."
                right = s[ci + 1:].strip()
                if right and right[0].islower():
                    right = right[0].upper() + right[1:]
                if not right.endswith((".", "!", "?")):
                    right = right + "."
                out.append(left)
                out.append(right)
                continue
            for conj in [" and ", " but ", " because ", " although ", " while ", " ve ", " ama ", " çünkü "]:
                idx = s.lower().find(conj)
                if idx > 5 and idx < len(s) - 5:
                    left = s[:idx] + "."
                    right = s[idx + len(conj):]
                    if right and right[0].islower():
                        right = right[0].upper() + right[1:]
                    if not right.endswith((".", "!", "?")):
                        right = right + "."
                    out.append(left)
                    out.append(right)
                    break
            else:
                out.append(s)
            continue
        out.append(s)
    return " ".join(out)


def rewrite_free(text: str, strict: bool = False, seed: int = 0, lang: str = "auto") -> str:
    if not text.strip():
        return text
    if lang == "auto":
        lang = detect_language(text)
    swaps, phrases, transitions, contractions = _rules(lang)
    original_text = text

    if not strict:
        text = _apply_phrase_swaps(text, phrases)
    text = _apply_word_swaps(text, swaps)
    if not strict:
        text = _remove_leading_transitions(text, transitions)
        text = _apply_contractions(text, contractions)
        text = _split_long_sentences(text)

    if strict and len(text.split()) != len(original_text.split()):
        text = original_text
        text = _apply_word_swaps(text, swaps)
        if len(text.split()) != len(original_text.split()):
            text = original_text
    return text


def rewrite_text(text: str, strict: bool = False, seed: int = 0, lang: str = "auto", profile: str = "balanced") -> str:
    if lang == "auto":
        lang = detect_language(text)
    if profile == "conservative":
        # only word swaps
        spans = split_protected(text)
        new_spans = []
        for i, sp in enumerate(spans):
            if sp.protected:
                new_spans.append(sp)
                continue
            original = sp.text
            cleaned = _apply_word_swaps(original, _rules(lang)[0])
            # preserve boundaries
            prev_protected = (i > 0 and spans[i - 1].protected)
            next_protected = (i + 1 < len(spans) and spans[i + 1].protected)
            if prev_protected and original.startswith((" ", "\t")) and not cleaned.startswith((" ", "\t")):
                cleaned = " " + cleaned
            if next_protected and original.endswith((" ", "\t")) and not cleaned.endswith((" ", "\t")):
                cleaned = cleaned + " "
            new_spans.append(Span(text=cleaned, protected=False, kind="text"))
        return reassemble(new_spans)

    spans = split_protected(text)
    new_spans = []
    for i, sp in enumerate(spans):
        if sp.protected:
            new_spans.append(sp)
            continue
        original = sp.text
        cleaned = rewrite_free(original, strict=strict, seed=seed, lang=lang)
        prev_protected = (i > 0 and spans[i - 1].protected)
        next_protected = (i + 1 < len(spans) and spans[i + 1].protected)
        if prev_protected and original.startswith((" ", "\t")) and not cleaned.startswith((" ", "\t")):
            cleaned = " " + cleaned
        if next_protected and original.endswith((" ", "\t")) and not cleaned.endswith((" ", "\t")):
            cleaned = cleaned + " "
        new_spans.append(Span(text=cleaned, protected=False, kind="text"))
    return reassemble(new_spans)
