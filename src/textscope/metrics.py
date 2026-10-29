from __future__ import annotations

import math
import re
from collections import Counter


def word_count(text: str) -> int:
    return len(text.split())


def sentence_split(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


def sentence_lengths(text: str) -> list[int]:
    return [len(s.split()) for s in sentence_split(text)]


def burstiness(text: str) -> float:
    lens = sentence_lengths(text)
    if len(lens) < 2:
        return 0.0
    mean = sum(lens) / len(lens)
    if mean == 0:
        return 0.0
    var = sum((x - mean) ** 2 for x in lens) / len(lens)
    std = math.sqrt(var)
    return std / mean


def ttr(text: str) -> float:
    words = [w.lower().strip(".,!?;:\"'()[]") for w in text.split()]
    words = [w for w in words if w]
    if not words:
        return 0.0
    return len(set(words)) / len(words)


def shannon_entropy(seq: list) -> float:
    if not seq:
        return 0.0
    c = Counter(seq)
    n = len(seq)
    ent = 0.0
    for count in c.values():
        p = count / n
        if p > 0:
            ent -= p * math.log2(p)
    return ent


def char_entropy(text: str) -> float:
    return shannon_entropy(list(text))


def word_entropy(text: str) -> float:
    words = text.split()
    return shannon_entropy(words)


def trigram_repetition(text: str) -> float:
    words = text.split()
    if len(words) < 4:
        return 0.0
    tris = [" ".join(words[i:i+3]) for i in range(len(words)-2)]
    c = Counter(tris)
    repeated = sum(v - 1 for v in c.values() if v > 1)
    return repeated / len(tris) if tris else 0.0



COMMON_WORDS_EN = {"the", "be", "to", "of", "and", "a", "in", "that", "have", "i", "it", "for", "not", "on", "with", "he", "as", "you", "do", "at", "this", "but", "his", "by", "from", "they", "we", "say", "her", "she", "or", "an", "will", "my", "one", "all", "would", "there", "their", "what", "so", "up", "out", "if", "about", "who", "get", "which", "go", "me", "when", "make", "can", "like", "time", "no", "just", "him", "know", "take", "people", "into", "year", "your", "good", "some", "could", "them", "see", "other", "than", "then", "now", "look", "only", "come", "its", "over", "think", "also", "back", "after", "use", "two", "how", "our", "work", "first", "well", "way", "even", "new", "want", "because", "any", "these", "give", "day", "most", "us"}

COMMON_WORDS_TR = {"bir", "ve", "bu", "için", "ile", "de", "da", "ki", "gibi", "daha", "çok", "en", "az", "olarak", "olan", "var", "yok", "ama", "veya", "hem", "kadar", "sonra", "önce", "göre"}

def detect_lang_simple(text):
    tr_chars = set("çğıöşüÇĞİÖŞÜ")
    if sum(1 for c in text if c in tr_chars) >= 3:
        return "tr"
    return "en"

def rare_word_ratio(text, lang=None):
    if lang is None:
        lang = detect_lang_simple(text)
    common = COMMON_WORDS_TR if lang == "tr" else COMMON_WORDS_EN
    words = [w.lower().strip(".,!?;:\"'()[]") for w in text.split()]
    words = [w for w in words if w and w.isalpha()]
    if not words:
        return 0.0
    rare = sum(1 for w in words if w not in common)
    return rare / len(words)

def sentence_length_variance(text):
    lens = sentence_lengths(text)
    if len(lens) < 2:
        return 0.0
    mean = sum(lens)/len(lens)
    return sum((x-mean)**2 for x in lens)/len(lens)

def report(text: str) -> dict:
    sl = sentence_lengths(text)
    lang = detect_lang_simple(text)
    return {
        "word_count": word_count(text),
        "sentence_count": len(sl),
        "language": lang,
        "avg_sentence_length": (sum(sl) / len(sl)) if sl else 0.0,
        "sentence_length_std": (math.sqrt(sum((x - (sum(sl)/len(sl)))**2 for x in sl)/len(sl)) if sl else 0.0),
        "burstiness_cv": burstiness(text),
        "type_token_ratio": ttr(text),
        "char_entropy": char_entropy(text),
        "word_entropy": word_entropy(text),
        "trigram_repetition": trigram_repetition(text),
        "rare_word_ratio": rare_word_ratio(text, lang),
        "sentence_length_variance": sentence_length_variance(text),
    }
