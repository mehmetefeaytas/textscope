from __future__ import annotations

import random
import re

from .protected import split_protected

# ---------- English rules ----------

# Formal / AI-typical wording -> plainer wording. Inflected forms are listed
# explicitly because a stem swap ("leverage") would miss "leverages".
WORD_SWAPS_EN = {
    # -- verbs: the classic LLM vocabulary
    "delve": "dig", "delves": "digs", "delved": "dug", "delving": "digging",
    "utilize": "use", "utilizes": "uses", "utilized": "used", "utilizing": "using",
    "utilization": "use", "leveraging": "using",
    "leverage": "use", "leverages": "uses", "leveraged": "used",
    "facilitate": "help", "facilitates": "helps", "facilitated": "helped",
    "facilitating": "helping",
    "foster": "build", "fosters": "builds", "fostered": "built", "fostering": "building",
    "bolster": "boost", "bolsters": "boosts", "bolstered": "boosted",
    "bolstering": "boosting",
    "underscore": "highlight", "underscores": "highlights",
    "underscored": "highlighted", "underscoring": "highlighting",
    "streamline": "simplify", "streamlines": "simplifies",
    "streamlined": "simplified", "streamlining": "simplifying",
    "optimize": "improve", "optimizes": "improves", "optimized": "improved",
    "optimizing": "improving",
    "enhance": "improve", "enhances": "improves", "enhanced": "improved",
    "enhancing": "improving", "enhancement": "improvement",
    "demonstrate": "show", "demonstrates": "shows", "demonstrated": "showed",
    "demonstrating": "showing",
    "illustrate": "show", "illustrates": "shows", "illustrated": "showed",
    "illustrating": "showing",
    "elucidate": "explain", "elucidates": "explains", "elucidated": "explained",
    "exemplify": "show", "exemplifies": "shows", "exemplified": "showed",
    "delineate": "outline", "delineates": "outlines", "delineated": "outlined",
    "elaborate": "expand", "elaborates": "expands", "elaborated": "expanded",
    "encompass": "cover", "encompasses": "covers", "encompassed": "covered",
    "constitute": "make up", "constitutes": "makes up", "constituted": "made up",
    "necessitate": "need", "necessitates": "needs", "necessitated": "needed",
    "commence": "start", "commences": "starts", "commenced": "started",
    "terminate": "end", "terminates": "ends", "terminated": "ended",
    "endeavor": "try", "endeavors": "tries", "endeavored": "tried",
    "endeavour": "try", "endeavours": "tries",
    "ascertain": "find out", "ascertains": "finds out",
    "ameliorate": "improve", "ameliorates": "improves",
    "mitigate": "reduce", "mitigates": "reduces", "mitigated": "reduced",
    "augment": "increase", "augments": "increases", "augmented": "increased",
    "procure": "get", "procures": "gets", "procured": "got",
    "obtain": "get", "obtains": "gets", "obtained": "got", "obtaining": "getting",
    "implement": "apply", "implements": "applies", "implemented": "applied",
    "implementing": "applying",
    "harness": "use", "harnesses": "uses", "harnessed": "used",
    "spearhead": "lead", "spearheads": "leads", "spearheaded": "led",
    "champion": "support", "champions": "supports", "championed": "supported",
    "elevate": "raise", "elevates": "raises", "elevated": "raised",
    "elevating": "raising",
    "empower": "enable", "empowers": "enables", "empowered": "enabled",
    "empowering": "enabling",
    "unlock": "open", "unlocks": "opens", "unlocked": "opened",
    "unleash": "release", "unleashes": "releases", "unleashed": "released",
    "revolutionize": "change", "revolutionizes": "changes",
    "revolutionized": "changed",
    "navigate": "handle", "navigates": "handles", "navigated": "handled",
    "embark": "start", "embarks": "starts", "embarked": "started",
    "disseminate": "share", "disseminates": "shares", "disseminated": "shared",
    "advocate": "back", "advocates": "backs", "advocated": "backed",
    "cultivate": "grow", "cultivates": "grows", "cultivated": "grew",
    "orchestrate": "run", "orchestrates": "runs", "orchestrated": "ran",
    "substantiate": "back up", "substantiates": "backs up",
    "transcend": "go beyond", "transcends": "goes beyond",
    "catalyze": "drive", "catalyzes": "drives",
    "juxtapose": "compare", "juxtaposes": "compares",
    "galvanize": "push", "galvanizes": "pushes",
    "operationalize": "run", "operationalizes": "runs",
    "contextualize": "frame", "contextualizes": "frames",

    # -- adjectives
    "multifaceted": "complex", "nuanced": "subtle", "pivotal": "key",
    "crucial": "important", "vital": "essential", "paramount": "top",
    "robust": "strong", "comprehensive": "full", "meticulous": "careful",
    "seamless": "smooth", "groundbreaking": "new", "transformative": "big",
    "holistic": "whole",

    # -- nouns
    "tapestry": "mix", "paradigm": "model", "synergy": "teamwork",
    "ecosystem": "system", "landscape": "field", "realm": "area",
    "plethora": "many", "myriad": "many",

    # -- connectors and hedges
    "furthermore": "also", "moreover": "also", "additionally": "also",
    "consequently": "so", "therefore": "so", "nevertheless": "still",
    "nonetheless": "still", "ultimately": "finally", "subsequently": "later",
    "previously": "before", "currently": "now", "approximately": "about",
    "numerous": "many", "various": "different", "additional": "more",
    "sufficient": "enough", "importantly": "above all", "interestingly": "oddly",
}

PHRASE_SWAPS_EN = [
    # hedging openers
    (r"\bit is important to note that\b", "note that"),
    (r"\bit is worth noting that\b", "note that"),
    (r"\bit should be noted that\b", "note that"),
    (r"\bit is worth mentioning that\b", "note that"),
    (r"\bit is essential to note that\b", "note that"),
    (r"\bit is crucial to note that\b", "note that"),
    (r"\bit is clear that\b", "clearly,"),
    (r"\bit can be seen that\b", "clearly,"),
    (r"\bthere is no doubt that\b", "undoubtedly,"),
    (r"\bit has been observed that\b", "observations show that"),
    (r"\bresearch has shown that\b", "studies show that"),
    (r"\bstudies have shown that\b", "studies show that"),
    # role / importance
    (r"\bplays a crucial role in\b", "matters for"),
    (r"\bplays a vital role in\b", "matters for"),
    (r"\bplays a key role in\b", "matters for"),
    (r"\bplays a critical role in\b", "matters for"),
    (r"\bplays a significant role in\b", "matters for"),
    (r"\bplays an important role in\b", "matters for"),
    (r"\bserves as a\b", "is a"), (r"\bserves as an\b", "is an"),
    (r"\bserves to\b", "helps"),
    (r"\bis characterized by\b", "shows"),
    # quantity
    (r"\ba wide range of\b", "many"), (r"\ba variety of\b", "various"),
    (r"\ba large number of\b", "many"), (r"\ba small number of\b", "a few"),
    (r"\ba significant number of\b", "many"),
    (r"\bthe vast majority of\b", "most"), (r"\bthe majority of\b", "most"),
    (r"\ba considerable amount of\b", "a lot of"),
    (r"\ba number of\b", "several"),
    # time
    (r"\bin recent years\b", "recently"),
    (r"\bin today's society\b", "today"),
    (r"\bat this point in time\b", "now"),
    (r"\bat the present time\b", "now"),
    (r"\bin the near future\b", "soon"),
    (r"\bon a regular basis\b", "regularly"),
    (r"\bon a daily basis\b", "daily"),
    (r"\bin a timely manner\b", "on time"),
    # cause / purpose
    (r"\bin order to\b", "to"),
    (r"\bdue to the fact that\b", "because"),
    (r"\bas a result of\b", "because of"),
    (r"\bas a consequence of\b", "because of"),
    (r"\bin spite of the fact that\b", "although"),
    (r"\bdespite the fact that\b", "although"),
    (r"\bregardless of the fact that\b", "although"),
    (r"\bin light of the fact that\b", "since"),
    (r"\bfor the purpose of\b", "to"),
    (r"\bwith the aim of\b", "to"),
    (r"\bwith the goal of\b", "to"),
    (r"\bfor the reason that\b", "because"),
    # place / scope
    (r"\bwith regard to\b", "about"), (r"\bwith respect to\b", "about"),
    (r"\bin terms of\b", "for"), (r"\bin the context of\b", "in"),
    (r"\bin the field of\b", "in"), (r"\bin the realm of\b", "in"),
    (r"\bin the area of\b", "in"), (r"\bwhen it comes to\b", "for"),
    (r"\bon the basis of\b", "based on"), (r"\bin the absence of\b", "without"),
    (r"\bin the presence of\b", "with"),
    # idioms
    (r"\bas a matter of fact\b", "in fact"),
    (r"\bat the end of the day\b", "ultimately"),
    (r"\bfirst and foremost\b", "first"),
    (r"\bin the majority of cases\b", "usually"),
    (r"\bfor the most part\b", "mostly"),
    # light verb + noun
    (r"\bmake use of\b", "use"),
    (r"\btake into consideration\b", "consider"),
    (r"\btake into account\b", "consider"),
    (r"\bcarry out\b", "do"),
    (r"\bis able to\b", "can"),
    (r"\bhas the ability to\b", "can"),
]

LEADING_TRANSITIONS_EN = [
    "moreover", "furthermore", "additionally", "in addition", "besides",
    "consequently", "therefore", "thus", "hence", "accordingly",
    "nevertheless", "nonetheless", "however", "meanwhile", "similarly",
    "likewise", "conversely", "instead", "in turn", "as a result",
    "for this reason", "in other words", "that said", "that being said",
    "all things considered", "by and large", "on balance",
    "in conclusion", "to conclude", "in summary", "to summarize",
    "to sum up", "in a nutshell", "in essence", "ultimately", "overall",
    "firstly", "secondly", "thirdly", "lastly", "finally",
    "importantly", "notably", "significantly", "interestingly",
    "surprisingly", "on the other hand", "on the contrary",
]

CONTRACTIONS_EN = [
    (r"\bdo not\b", "don't"), (r"\bcannot\b", "can't"), (r"\bcan not\b", "can't"),
    (r"\bit is\b", "it's"), (r"\bthat is\b", "that's"), (r"\bwe are\b", "we're"),
    (r"\bthey are\b", "they're"), (r"\byou are\b", "you're"), (r"\bi am\b", "I'm"),
    (r"\bhe is\b", "he's"), (r"\bshe is\b", "she's"), (r"\bthere is\b", "there's"),
    (r"\bhere is\b", "here's"), (r"\bwhat is\b", "what's"), (r"\bwho is\b", "who's"),
    (r"\bwill not\b", "won't"), (r"\bwould not\b", "wouldn't"),
    (r"\bshould not\b", "shouldn't"), (r"\bcould not\b", "couldn't"),
    (r"\bmust not\b", "mustn't"), (r"\bneed not\b", "needn't"),
    (r"\bis not\b", "isn't"), (r"\bare not\b", "aren't"),
    (r"\bwas not\b", "wasn't"), (r"\bwere not\b", "weren't"),
    (r"\bhas not\b", "hasn't"), (r"\bhave not\b", "haven't"),
    (r"\bhad not\b", "hadn't"), (r"\bdoes not\b", "doesn't"),
    (r"\bdid not\b", "didn't"), (r"\blet us\b", "let's"),
    (r"\bwe will\b", "we'll"), (r"\bthey will\b", "they'll"),
    (r"\byou will\b", "you'll"), (r"\bhe will\b", "he'll"),
    (r"\bshe will\b", "she'll"), (r"\bi will\b", "I'll"),
    (r"\bwe have\b", "we've"), (r"\bthey have\b", "they've"),
    (r"\byou have\b", "you've"), (r"\bi have\b", "I've"),
    (r"\bwe would\b", "we'd"), (r"\bthey would\b", "they'd"),
    (r"\bi would\b", "I'd"), (r"\byou would\b", "you'd"),
]

# ---------- extra rules for --profile aggressive ----------

EXTRA_WORD_SWAPS_EN = {
    "substantial": "large", "substantially": "largely", "intricate": "complex",
    "intricacies": "details", "unprecedented": "new", "cutting-edge": "modern",
    "state-of-the-art": "modern", "rapidly evolving": "changing",
    "ever-evolving": "changing", "in today's world": "today",
    "significant": "notable", "significantly": "notably",
    "furthermore": "also", "nevertheless": "still",
    "methodology": "method", "methodologies": "methods",
    "utilization": "use", "implementation": "use",
}

EXTRA_PHRASE_SWAPS_EN = [
    (r"\bin today's (?:rapidly )?(?:evolving|changing) (?:world|landscape|field)\b", "today"),
    (r"\bin the ever-(?:evolving|changing) (?:world|landscape|field) of\b", "in"),
    (r"\bthe fact that\b", "that"),
    (r"\bhas the ability to\b", "can"),
    (r"\bmake a decision\b", "decide"),
    (r"\bit is essential to\b", "you need to"),
    (r"\bthe vast majority of\b", "most"),
    (r"\bin the process of\b", "while"),
]

EXTRA_WORD_SWAPS_TR = {
    "önemli ölçüde": "büyük oranda", "karmaşık yapı": "yapı",
    "hızlı bir şekilde": "hızla", "büyük önem taşımaktadır": "önemlidir",
    "söz konusu": "adı geçen", "her bir": "her",
}

# Alternative replacements per word. ``--seed`` picks one of them, so retrying
# with a different seed produces genuinely different text instead of a no-op.
WORD_VARIANTS_EN = {
    "delve": ("dig", "look", "probe"),
    "comprehensive": ("full", "complete", "broad"),
    "crucial": ("important", "key", "central"),
    "pivotal": ("key", "central", "critical"),
    "leverage": ("use", "apply", "draw on"),
    "utilize": ("use", "apply", "employ"),
    "facilitate": ("help", "aid", "support"),
    "robust": ("strong", "solid", "sturdy"),
    "foster": ("build", "grow", "encourage"),
    "moreover": ("also", "besides", "what is more"),
    "furthermore": ("also", "besides", "on top of that"),
    "additional": ("more", "extra", "further"),
    "numerous": ("many", "plenty of", "several"),
    "enhance": ("improve", "boost", "sharpen"),
    "demonstrate": ("show", "prove", "make clear"),
    "mitigate": ("reduce", "ease", "limit"),
}

WORD_VARIANTS_TR = {
    "kapsamlı": ("geniş", "detaylı", "kapsayıcı"),
    "verimli": ("faydalı", "etkin", "üretken"),
    "etkin": ("etkili", "verimli", "işlevsel"),
    "sürdürülebilir": ("kalıcı", "uzun ömürlü", "devamlı"),
    "stratejik": ("planlı", "bilinçli", "hedefli"),
    "kritik": ("önemli", "yaşamsal", "belirleyici"),
    "potansiyel": ("olası", "muhtemel", "beklenen"),
    "global": ("küresel", "dünya çapında", "genel"),
    "literatür": ("yazın", "alan yazını"),
    "metodoloji": ("yöntem", "yaklaşım"),
}

# ---------- Turkish rules ----------

# Academic / AI-typical Turkish -> plain Turkish. Turkish is agglutinative, so
# common inflected forms are listed next to their base form.
WORD_SWAPS_TR = {
    # sıfatlar
    "kapsamlı": "geniş", "etkin": "etkili", "verimli": "faydalı",
    "sürdürülebilir": "kalıcı", "bütüncül": "bütün", "holistik": "bütüncül",
    "kayda değer": "önemli", "dikkat çekici": "ilginç", "kritik": "önemli",
    "optimal": "en iyi", "optimum": "en iyi", "maksimum": "en yüksek",
    "minimum": "en düşük", "proaktif": "önceden", "inovatif": "yenilikçi",
    "multidisipliner": "çok alanlı", "disiplinler arası": "çok alanlı",
    "entegre": "bütünleşik", "efektif": "etkili", "global": "küresel",
    "potansiyel": "olası", "dinamik": "hareketli", "robust": "güçlü",
    "kapsayıcı": "geniş kapsamlı", "stratejik": "planlı",
    # isimler
    "paradigma": "yaklaşım", "sinergi": "işbirliği", "ekosistem": "sistem",
    "metodoloji": "yöntem", "metodolojik": "yöntemsel", "parametre": "değişken",
    "kriter": "ölçüt", "kriterler": "ölçütler", "perspektif": "bakış açısı",
    "vizyon": "bakış", "misyon": "amaç", "trend": "eğilim",
    "literatür": "yazın", "hipotez": "varsayım", "entegrasyon": "bütünleşme",
    "adaptasyon": "uyum", "implementasyon": "uygulama",
    "optimizasyon": "iyileştirme", "inovasyon": "yenilik",
    "maksimize": "artır", "minimize": "azalt", "optimize": "geliştir",
    # academic verb phrases
    "gerçekleştirmek": "yapmak", "gerçekleştirilen": "yapılan",
    "gerçekleştirilmesi": "yapılması", "gerçekleştirilmiştir": "yapılmıştır",
    "gerçekleştirilmektedir": "yapılmaktadır",
    "gerçekleştirilerek": "yapılarak",
    # derece / ölçü zarfları
    "oldukça": "epey", "son derece": "çok", "bir hayli": "oldukça",
    "hemen hemen": "neredeyse", "büyük ölçüde": "büyük oranda",
    # kalıplaşmış ifadeler
    "bu doğrultuda": "bu yönde", "söz konusu": "adı geçen",
    "dikkate alındığında": "düşünüldüğünde",
    "göz önünde bulundurulduğunda": "düşünüldüğünde",
    "veriler ışığında": "verilere göre",
    "literatür incelendiğinde": "yazına bakıldığında",
    "çalışmanın amacı": "amaç", "çalışmanın kapsamı": "kapsam",
    "halihazırda": "şu anda",
}

PHRASE_SWAPS_TR = [
    # formalizers
    (r"\bbelirtmek gerekir ki\b", "belirtelim,"),
    (r"\bifade etmek gerekir\b", "belirtelim"),
    (r"\bvurgulamak gerekir\b", "vurgulayalım"),
    (r"\bdikkat çekmek gerekir ki\b", "dikkat çekelim,"),
    (r"\bunutulmamalıdır ki\b", "unutmayın,"),
    (r"\bbilinmelidir ki\b", "bilinmeli,"),
    (r"\baçıkça görülmektedir\b", "açıkça görülüyor"),
    # findings
    (r"\belde edilen bulgular\b", "bulgular"),
    (r"\baraştırma sonuçları\b", "sonuçlar"),
    (r"\bsonuçlar göstermektedir\b", "sonuçlar gösteriyor"),
    (r"\bveriler göstermektedir\b", "veriler gösteriyor"),
    (r"\bçalışma kapsamında\b", "bu çalışmada"),
    (r"\bbu çalışma kapsamında\b", "bu çalışmada"),
    (r"\bliteratürde\b", "yazında"),
    (r"\bönerilmektedir\b", "öneriliyor"),
    (r"\bdeğerlendirilmektedir\b", "değerlendiriliyor"),
    (r"\bgerekmektedir\b", "gerekiyor"),
    (r"\bsağlamaktadır\b", "sağlıyor"),
    (r"\bgöstermektedir\b", "gösteriyor"),
    (r"\bifade edilmektedir\b", "ifade ediliyor"),
    (r"\bkabul edilmektedir\b", "kabul ediliyor"),
    (r"\bele alınmaktadır\b", "ele alınıyor"),
    (r"\byer almaktadır\b", "yer alıyor"),
    (r"\bortaya konmaktadır\b", "ortaya konuyor"),
    (r"\bortaya koymaktadır\b", "ortaya koyuyor"),
    (r"\bönem taşımaktadır\b", "önem taşıyor"),
    (r"\brol oynamaktadır\b", "rol oynuyor"),
    (r"\bönemli bir rol oynamaktadır\b", "etkili olmaktadır"),
    # optimizasyon
    (r"\boptimize edebiliriz\b", "geliştirebiliriz"),
    (r"\boptimize edebilir\b", "geliştirebilir"),
    (r"\boptimize edilmesi\b", "iyileştirilmesi"),
    # connectors
    (r"\bbu bağlamda\b", "bu konuda"),
    (r"\bbu noktada\b", "burada"),
    (r"\bbuna ek olarak\b", "ayrıca"),
    (r"\bbununla birlikte\b", "ama"),
    (r"\bdiğer yandan\b", "öte yandan"),
    (r"\bdiğer taraftan\b", "öte yandan"),
    (r"\bgenel olarak\b", "genelde"),
    (r"\bgenel anlamda\b", "genelde"),
    (r"\bbir başka deyişle\b", "yani"),
    (r"\bbaşka bir deyişle\b", "yani"),
    (r"\bbir başka ifadeyle\b", "yani"),
    (r"\bsonuç olarak\b", "sonuçta"),
    (r"\bsonuç itibarıyla\b", "sonuçta"),
    (r"\bözetle\b", "kısaca"),
    (r"\bkısacası\b", "kısaca"),
    (r"\buzun lafın kısası\b", "kısaca"),
    (r"\bbu çerçevede\b", "bu yönde"),
    (r"\bbu minvalde\b", "bu yönde"),
    (r"\bher şeyden önce\b", "önce"),
    (r"\ben nihayetinde\b", "sonunda"),
    (r"\bşu aşamada\b", "şimdi"),
    (r"\bilerleyen dönemlerde\b", "sonra"),
    (r"\byakın gelecekte\b", "yakında"),
    (r"\bbu nedenle\b", "bu yüzden"),
    (r"\bbu sebeple\b", "bu yüzden"),
    (r"\bdolayısıyla\b", "bu yüzden"),
]

LEADING_TRANSITIONS_TR = [
    "sonuç olarak", "sonuç itibarıyla", "bu bağlamda", "bu noktada",
    "bu doğrultuda", "bu çerçevede", "bu kapsamda", "bu minvalde",
    "ayrıca", "üstelik", "bununla birlikte", "buna ek olarak",
    "bunun yanı sıra", "bunun yanında", "diğer yandan", "öte yandan",
    "öte taraftan", "diğer taraftan", "buna karşın", "buna rağmen",
    "özetle", "kısacası", "genel olarak", "genel anlamda",
    "bir başka deyişle", "başka bir deyişle", "dolayısıyla",
    "bu nedenle", "bu sebeple", "buna göre", "bu durumda",
    "ilk olarak", "ikinci olarak", "üçüncü olarak", "son olarak",
    "halihazırda", "şu aşamada",
]

# Turkish does not contract the way English does; formal verb endings are
# softened by the -mektedir/-mıştır rules below instead.
CONTRACTIONS_TR: list[tuple[str, str]] = []
_TR_CHARS = frozenset("çğıöşüÇĞİÖŞÜ")

_TR_STOPWORDS = frozenset({
    "bir", "ve", "bu", "için", "ile", "da", "de", "ki", "gibi", "daha",
    "çok", "en", "az", "olarak", "olan", "var", "yok", "ama", "veya",
    "hem", "kadar", "sonra", "önce", "göre", "şu", "her", "değil",
    "üzerinde", "arasında", "tarafından", "nedeniyle", "ancak", "çünkü",
    "eğer", "ise", "diye", "bile", "hiç", "sadece", "yine", "artık",
    "böyle", "şöyle", "hangi", "nasıl", "neden", "çalışma", "sonuç",
    "veri", "veriler", "yöntem", "analiz", "değer", "oran", "durum",
})


def detect_language(text: str) -> str:
    """Detect Turkish vs English with no external dependency.

    Turkish is recognised by its special letters *and* by a ratio of common
    function words, so ASCII-only Turkish ("calisma") is still detected.
    """
    if not text.strip():
        return "en"
    tr_char_hits = sum(1 for ch in text if ch in _TR_CHARS)
    tokens = re.findall(r"[^\W\d_]+", text.lower())
    if not tokens:
        return "en"
    tr_word_hits = sum(1 for t in tokens if t in _TR_STOPWORDS)
    ratio = tr_word_hits / len(tokens)
    if tr_char_hits >= 2 and ratio >= 0.03:
        return "tr"
    if ratio >= 0.08:
        return "tr"
    if tr_char_hits >= 4:
        return "tr"
    return "en"


def _rules(lang: str):
    if lang == "tr":
        return (WORD_SWAPS_TR, PHRASE_SWAPS_TR, LEADING_TRANSITIONS_TR, CONTRACTIONS_TR)
    return (WORD_SWAPS_EN, PHRASE_SWAPS_EN, LEADING_TRANSITIONS_EN, CONTRACTIONS_EN)


def _upper_first(text: str, lang: str = "en") -> str:
    """Uppercase the first letter, honouring Turkish i/ı."""
    if not text:
        return text
    first = text[0]
    if lang == "tr" and first == "i":
        first = "İ"
    elif lang == "tr" and first == "ı":
        first = "I"
    else:
        first = first.upper()
    return first + text[1:]


def _preserve_case(original: str, replacement: str, lang: str = "en") -> str:
    if original and replacement and original[0].isupper():
        return _upper_first(replacement, lang)
    return replacement


def _apply_word_swaps(text: str, swaps: dict, lang: str = "en") -> str:
    if not swaps:
        return text
    pattern = r"\b(" + "|".join(re.escape(k) for k in sorted(swaps, key=len, reverse=True)) + r")\b"
    def repl(m):
        w = m.group(0)
        low = w.lower()
        if low in swaps:
            return _preserve_case(w, swaps[low], lang)
        return w
    return re.sub(pattern, repl, text, flags=re.IGNORECASE)


def _apply_phrase_swaps(text: str, swaps: list, lang: str = "en") -> str:
    for pat, rep in swaps:
        def repl(m, rep=rep):
            return _preserve_case(m.group(0), rep, lang)
        text = re.sub(pat, repl, text, flags=re.IGNORECASE)
    return text


def _remove_leading_transitions(text: str, transitions: list, lang: str = "en") -> str:
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
                        s2 = s2[:idx] + _upper_first(stripped, lang)
                break
        out.append(s2)
    return " ".join(out)


def _apply_contractions(text: str, contractions: list, lang: str = "en") -> str:
    def repl(m, rep):
        return _preserve_case(m.group(0), rep, lang)

    for pat, rep in contractions:
        text = re.sub(pat, lambda m, r=rep: repl(m, r), text, flags=re.IGNORECASE)
    return text


# ---------- Turkish verb forms ----------
#
# Turkish academic prose is dominated by "-mektedir" and "-mıştır". Swapping
# whole word lists is not enough because the suffix carries the tense. These
# rules convert the suffix generically while keeping it one word -> one word,
# so --strict word counts still hold.

_TR_VOWELS = "aeıioöuü"
_TR_HARMONY = {"a": "ı", "ı": "ı", "e": "i", "i": "i",
               "o": "u", "u": "u", "ö": "ü", "ü": "ü"}
_TR_VOICELESS = frozenset("çfhkpsşt")
_TR_PROGRESSIVE_STEMS = {"et": "ed", "git": "gid", "tat": "tad"}
_TR_COPULA_EXCEPTIONS = frozenset({"müdür", "kudur", "hüdür"})
_TR_WORD_CHARS = "A-Za-zÇĞİÖŞÜçğıöşü"

_TR_PROGRESSIVE_RE = re.compile(
    rf"\b([{_TR_WORD_CHARS}]{{2,}}?)(mekte|makta)(dır|dir)(ler|lar)?\b")
_TR_PAST_RE = re.compile(
    rf"\b([{_TR_WORD_CHARS}]{{2,}}?)(mış|miş|muş|müş)(lar|ler)?(dır|dir|dur|dür|tır|tir|tur|tür)\b")
_TR_FUTURE_RE = re.compile(
    rf"\b([{_TR_WORD_CHARS}]{{2,}}?)(ecek|acak)(lar|ler)?(tır|tir|tur|tür)\b")
_TR_NECESSITY_RE = re.compile(
    rf"\b([{_TR_WORD_CHARS}]{{2,}}?)(malı|meli)(dır|dir)\b")
_TR_COPULA_RE = re.compile(
    rf"\b([{_TR_WORD_CHARS}]{{3,}}?)(dır|dir|dur|dür)\b")


def _last_vowel(word: str) -> str:
    for ch in reversed(word):
        if ch in _TR_VOWELS:
            return ch
    return "ı"


def _progressive(stem: str) -> str:
    """gel- -> geliyor, yapıl- -> yapılıyor, oku- -> okuyor, et- -> ediyor."""
    if stem[-1] in _TR_VOWELS:
        base = stem[:-1]
        vowel = _TR_HARMONY[stem[-1]]
    else:
        base = _TR_PROGRESSIVE_STEMS.get(stem, stem)
        vowel = _TR_HARMONY[_last_vowel(stem)]
    return base + vowel + "yor"


def _simple_past(stem: str) -> str:
    """yapıl- -> yapıldı, et- -> etti, oku- -> okudu."""
    vowel = _TR_HARMONY[_last_vowel(stem)]
    consonant = "t" if stem[-1] in _TR_VOICELESS else "d"
    return stem + consonant + vowel


def _apply_turkish_forms(text: str, aggressive: bool = False) -> str:
    """Soften formal Turkish verb endings without changing the word count."""
    def restore(original: str, result: str) -> str:
        return _upper_first(result, "tr") if original[:1].isupper() else result

    def progressive(m):
        result = _progressive(m.group(1).lower())
        if m.group(4):
            result += "lar"
        return restore(m.group(0), result)

    def past(m):
        result = _simple_past(m.group(1).lower())
        if m.group(3):
            result += "lar"
        return restore(m.group(0), result)

    def future(m):
        result = m.group(1).lower() + m.group(2)
        if m.group(3):
            result += "lar"
        return restore(m.group(0), result)

    def necessity(m):
        return restore(m.group(0), m.group(1).lower() + m.group(2))

    def copula(m):
        stem = m.group(1)
        if len(stem) < 3 or stem.lower() in _TR_COPULA_EXCEPTIONS:
            return m.group(0)
        return restore(m.group(0), stem)

    text = _TR_PROGRESSIVE_RE.sub(progressive, text)
    text = _TR_PAST_RE.sub(past, text)
    text = _TR_FUTURE_RE.sub(future, text)
    text = _TR_NECESSITY_RE.sub(necessity, text)
    if aggressive:
        text = _TR_COPULA_RE.sub(copula, text)
    return text


_DUP_WORD = re.compile(r"\b(\w+)([ \t]+)\1\b", re.IGNORECASE)

# Past-tense swaps can create impossible auxiliaries ("have showed"). Repair the
# handful of irregular verbs that the word table touches.
_EN_AUX_FIXES = [
    (r"\b(have|has|had|having|was|were|is|are|be|been|being)\s+showed\b", r"\1 shown"),
    (r"\b(have|has|had|having)\s+grew\b", r"\1 grown"),
    (r"\b(have|has|had|having)\s+ran\b", r"\1 run"),
    (r"\b(have|has|had|having)\s+went\b", r"\1 gone"),
    (r"\b(have|has|had|having)\s+dug\b", r"\1 dug"),
]


def _fix_english_grammar(text: str) -> str:
    for pattern, replacement in _EN_AUX_FIXES:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return _fix_articles(text)


_ARTICLE_RE = re.compile(r"\b(a|an|A|An)\s+([A-Za-z][A-Za-z'-]*)")
# words starting with a vowel letter but a consonant sound, and vice versa
_A_BEFORE_VOWEL = ("uni", "use", "usu", "uti", "ure", "uro", "eu", "one",
                   "once", "ubiq", "unanim", "ufo")
_AN_BEFORE_CONSONANT = ("hour", "honest", "honor", "honour", "heir")


def _fix_articles(text: str) -> str:
    """Repair "a important" -> "an important" after adjective swaps."""

    def repl(m: re.Match) -> str:
        article, word = m.group(1), m.group(2)
        low = word.lower()
        needs_an = low[0] in "aeiou" and not low.startswith(_A_BEFORE_VOWEL)
        needs_an = needs_an or low.startswith(_AN_BEFORE_CONSONANT)
        if needs_an and article.lower() == "a":
            article = "An" if article[0].isupper() else "an"
        elif not needs_an and article.lower() == "an":
            article = "A" if article[0].isupper() else "a"
        return f"{article} {word}"

    return _ARTICLE_RE.sub(repl, text)


_DUP_STARTERS = frozenset({"also", "besides", "however", "therefore", "thus",
                           "still", "so", "plus"})


def _dedupe_sentence_starters(text: str, lang: str = "en") -> str:
    """Avoid "Also, ... Also, ..." runs created by connector swaps."""
    sentences = _SENT_SPLIT.split(text)
    out: list[str] = []
    previous: str | None = None
    for sentence in sentences:
        m = re.match(r"(\s*)([A-Za-zÇĞİÖŞÜçğıöşü]+)(,\s+)", sentence)
        word = m.group(2).lower() if m else None
        if m and word == previous and word in _DUP_STARTERS:
            rest = sentence[m.end():]
            if rest.strip():
                sentence = m.group(1) + _upper_first(rest, lang)
        out.append(sentence)
        previous = word
    return " ".join(out)


def _collapse_duplicate_words(text: str) -> str:
    """Kill "Bu bu çalışmada" / "the the" artifacts left by phrase swaps."""
    previous = None
    while previous != text:
        previous = text
        text = _DUP_WORD.sub(lambda m: m.group(1), text)
    return text


_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")
_SPLIT_CONJUNCTIONS = (
    " and ", " but ", " because ", " although ", " while ",
    " ve ", " ama ", " çünkü ", " ancak ",
)


def _split_sentence(sentence: str, min_part: int, lang: str = "en") -> list[str] | None:
    """Split at a conjunction or comma, but only into two real clauses.

    Both halves must carry at least ``min_part`` words, otherwise we return None
    and keep the sentence intact. This is what stops the tool from turning
    "In today's evolving landscape, AI matters." into a 5-word fragment.
    """
    low = sentence.lower()
    cuts: list[tuple[int, int]] = []
    for conj in _SPLIT_CONJUNCTIONS:
        start = 0
        while (idx := low.find(conj, start)) != -1:
            cuts.append((idx, idx + len(conj)))
            start = idx + 1
    start = 0
    while (idx := sentence.find(",", start)) != -1:
        cuts.append((idx, idx + 1))
        start = idx + 1

    best: tuple[int, str, str] | None = None
    for cut_start, cut_end in cuts:
        left = sentence[:cut_start].strip()
        right = sentence[cut_end:].strip()
        if len(left.split()) < min_part or len(right.split()) < min_part:
            continue
        balance = abs(len(left.split()) - len(right.split()))
        if best is None or balance < best[0]:
            best = (balance, left, right)
    if best is None:
        return None

    _, left, right = best
    left = left.rstrip(",;:").rstrip() + "."
    right = _upper_first(right, lang)
    if not right.endswith((".", "!", "?")):
        right = right.rstrip(",;:").rstrip() + "."
    return [left, right]


def _split_long_sentences(text: str, min_part: int = 6, lang: str = "en") -> str:
    out: list[str] = []
    for sentence in _SENT_SPLIT.split(text):
        if len(sentence.split()) < 2 * min_part:
            out.append(sentence)
            continue
        parts = _split_sentence(sentence, min_part, lang)
        out.extend(parts if parts else [sentence])
    return " ".join(out)


def _pick_variants(swaps: dict, rng: random.Random, lang: str) -> dict:
    table = WORD_VARIANTS_TR if lang == "tr" else WORD_VARIANTS_EN
    return {k: (rng.choice(table[k]) if k in table else v) for k, v in swaps.items()}


def rewrite_free(text: str, strict: bool = False, seed: int = 0, lang: str = "auto",
                 aggressive: bool = False) -> str:
    if not text.strip():
        return text
    if lang == "auto":
        lang = detect_language(text)
    swaps, phrases, transitions, contractions = _rules(lang)
    original_text = text
    rng = random.Random(seed)
    swaps = _pick_variants(swaps, rng, lang)

    if aggressive:
        extra_swaps = EXTRA_WORD_SWAPS_TR if lang == "tr" else EXTRA_WORD_SWAPS_EN
        swaps = {**swaps, **extra_swaps}
        if lang != "tr":
            phrases = list(phrases) + EXTRA_PHRASE_SWAPS_EN

    if strict:
        # Only 1-word -> 1-word swaps are safe; multi-word replacements would
        # shift the count, so they are filtered out for --strict.
        safe_swaps = {k: v for k, v in swaps.items() if len(k.split()) == len(v.split())}
        text = _apply_word_swaps(text, safe_swaps, lang)
        if lang == "tr":
            text = _apply_turkish_forms(text, aggressive=aggressive)
        else:
            text = _fix_english_grammar(text)
        if len(text.split()) != len(original_text.split()):
            text = original_text
        return _collapse_duplicate_words(text)

    # --seed also picks the split threshold and whether contractions apply.
    min_part = 6 if aggressive else rng.choice([6, 7, 8])
    use_contractions = aggressive or rng.random() < 0.8

    text = _apply_phrase_swaps(text, phrases, lang)
    text = _apply_word_swaps(text, swaps, lang)
    if lang == "tr":
        text = _apply_turkish_forms(text, aggressive=aggressive)
    else:
        text = _fix_english_grammar(text)
    text = _remove_leading_transitions(text, transitions, lang)
    if use_contractions:
        text = _apply_contractions(text, contractions, lang)
    if lang != "tr":
        text = _dedupe_sentence_starters(text, lang)
    text = _split_long_sentences(text, min_part=min_part, lang=lang)
    return _collapse_duplicate_words(text)


_LINE_BREAK = re.compile(r"(\r\n|\n|\r)")


def _map_lines(text: str, transform) -> str:
    """Apply ``transform`` per line, keeping every newline in place.

    Rewriting a whole paragraph at once used to glue lines together, because the
    sentence splitter rejoined with spaces.
    """
    parts = _LINE_BREAK.split(text)
    out = []
    for part in parts:
        if _LINE_BREAK.fullmatch(part) or not part.strip():
            out.append(part)
            continue
        cleaned = transform(part)
        if not cleaned:
            out.append(part)
            continue
        lead = part[: len(part) - len(part.lstrip())]
        trail = part[len(part.rstrip()):]
        if lead and not cleaned.startswith(lead):
            cleaned = lead + cleaned.lstrip()
        if trail and not cleaned.endswith(trail):
            cleaned = cleaned.rstrip() + trail
        out.append(cleaned)
    return "".join(out)


def _rewrite_document(text: str, transform) -> str:
    """Protect first, then rewrite the prose line by line.

    Protection has to run on the whole document: a fenced code block or a
    ``\\begin{document}`` only makes sense across lines. The prose is still
    rewritten per line so the layout survives.
    """
    out = []
    for sp in split_protected(text):
        if sp.protected or not sp.text.strip():
            out.append(sp.text)
        else:
            out.append(_map_lines(sp.text, transform))
    return "".join(out)


def rewrite_text(text: str, strict: bool = False, seed: int = 0, lang: str = "auto", profile: str = "balanced") -> str:
    if not text:
        return text
    if lang == "auto":
        lang = detect_language(text)
    aggressive = profile == "aggressive"
    word_swaps = _rules(lang)[0]
    if aggressive:
        extra = EXTRA_WORD_SWAPS_TR if lang == "tr" else EXTRA_WORD_SWAPS_EN
        word_swaps = {**word_swaps, **extra}

    if profile == "conservative":
        selected = _pick_variants(word_swaps, random.Random(seed), lang)

        def transform(block: str) -> str:
            return _apply_word_swaps(block, selected, lang)
    else:
        def transform(block: str) -> str:
            return rewrite_free(block, strict=strict, seed=seed, lang=lang,
                                aggressive=aggressive)

    return _rewrite_document(text, transform)
