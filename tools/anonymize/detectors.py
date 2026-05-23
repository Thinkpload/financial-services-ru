"""
Детекторы PII/реквизитов для российских финдокументов.

Возвращают список (original_text, kind) — порядок не гарантируется.
Дедупликация и присвоение псевдонимов — в anonymize.py.
"""

import re
from typing import Iterable

# Российские реквизиты — порядок длины важен (длинные паттерны первыми,
# чтобы 20-значный счёт не съелся как ИНН-фрагмент).
PATTERNS: list[tuple[str, re.Pattern]] = [
    ("RS",    re.compile(r"\b\d{20}\b")),                          # расчётный счёт
    ("OGRNIP", re.compile(r"\b\d{15}\b")),                          # ОГРНИП
    ("OGRN",  re.compile(r"\b\d{13}\b")),                          # ОГРН
    ("INN12", re.compile(r"\b\d{12}\b")),                          # ИНН физлица/ИП
    ("INN10", re.compile(r"\b\d{10}\b")),                          # ИНН юрлица
    ("KPP",   re.compile(r"\b\d{9}\b")),                           # КПП
    ("BIK",   re.compile(r"\b04\d{7}\b")),                         # БИК (RU начинаются с 04)
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    ("PHONE", re.compile(r"(?:\+7|8)[\s\-(]*\d{3}[\s\-)]*\d{3}[\s\-]*\d{2}[\s\-]*\d{2}")),
]

# Формы собственности для regex-поиска организаций (fallback без natasha).
ORG_FORM = re.compile(
    r'(?:ООО|ОАО|ЗАО|ПАО|АО|НКО|ГК|ИП)\s+["«]?([А-ЯЁA-Z][\w\-\s.]{1,60}?)["»]?(?=[\s,.;:)\n]|$)',
    re.UNICODE,
)


def detect_regex(text: str) -> list[tuple[str, str]]:
    """Детектит реквизиты и emails/телефоны по regex. Возвращает [(match, kind), ...]."""
    found: list[tuple[str, str]] = []
    for kind, pat in PATTERNS:
        for m in pat.finditer(text):
            found.append((m.group(0), kind))
    for m in ORG_FORM.finditer(text):
        # Сохраняем полное совпадение включая форму ("ООО Ромашка")
        found.append((m.group(0).strip(), "ORG"))
    return found


_natasha_cache = None


def _get_natasha():
    """Ленивая инициализация natasha (тяжёлая загрузка моделей)."""
    global _natasha_cache
    if _natasha_cache is False:
        return None
    if _natasha_cache is not None:
        return _natasha_cache
    try:
        from natasha import (
            Segmenter, MorphVocab, NewsEmbedding,
            NewsMorphTagger, NewsNERTagger, Doc,
        )
    except ImportError:
        _natasha_cache = False
        return None
    emb = NewsEmbedding()
    _natasha_cache = {
        "segmenter": Segmenter(),
        "morph_vocab": MorphVocab(),
        "morph_tagger": NewsMorphTagger(emb),
        "ner_tagger": NewsNERTagger(emb),
        "Doc": Doc,
    }
    return _natasha_cache


def detect_natasha(text: str) -> list[tuple[str, str]]:
    """
    Детектит ФИО (PER) и организации (ORG) через natasha NER.
    Возвращает [] если natasha не установлена.
    """
    n = _get_natasha()
    if not n:
        return []
    doc = n["Doc"](text)
    doc.segment(n["segmenter"])
    doc.tag_morph(n["morph_tagger"])
    doc.tag_ner(n["ner_tagger"])
    out: list[tuple[str, str]] = []
    for span in doc.spans:
        if span.type in ("PER", "ORG", "LOC"):
            out.append((span.text, span.type))
    return out


def detect_all(text: str) -> list[tuple[str, str]]:
    """Объединяет regex + natasha. Дедуп — на стороне вызывающего кода."""
    return detect_regex(text) + detect_natasha(text)
