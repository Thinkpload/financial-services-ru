"""
Детекторы PII/реквизитов для российских финдокументов.

Возвращают список (original_text, kind) — порядок не гарантируется.
Дедупликация и присвоение псевдонимов — в anonymize.py.
"""

import re
from typing import Iterable


# --- Валидаторы контрольных сумм (без них регекс ловит любые числа) ---------

def _valid_inn10(s: str) -> bool:
    if len(s) != 10 or not s.isdigit():
        return False
    weights = [2, 4, 10, 3, 5, 9, 4, 6, 8]
    check = sum(int(s[i]) * weights[i] for i in range(9)) % 11 % 10
    return check == int(s[9])


def _valid_inn12(s: str) -> bool:
    if len(s) != 12 or not s.isdigit():
        return False
    w1 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8, 0]
    w2 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8, 0]
    c1 = sum(int(s[i]) * w1[i] for i in range(11)) % 11 % 10
    c2 = sum(int(s[i]) * w2[i] for i in range(12)) % 11 % 10
    return c1 == int(s[10]) and c2 == int(s[11])


def _valid_ogrn(s: str) -> bool:
    if len(s) != 13 or not s.isdigit():
        return False
    return int(s[:12]) % 11 % 10 == int(s[12])


def _valid_ogrnip(s: str) -> bool:
    if len(s) != 15 or not s.isdigit():
        return False
    return int(s[:14]) % 13 % 10 == int(s[14])


VALIDATORS = {
    "INN10":  _valid_inn10,
    "INN12":  _valid_inn12,
    "OGRN":   _valid_ogrn,
    "OGRNIP": _valid_ogrnip,
}

# Паттерны с keyword-контекстом: реквизит ищется ТОЛЬКО если перед ним
# в пределах KEYWORD_WINDOW символов стоит соответствующее ключевое слово.
# Это убирает массовые false positives на финансовых числах.
KEYWORD_WINDOW = 30

KEYWORDED: list[tuple[str, re.Pattern, re.Pattern]] = [
    ("INN10",  re.compile(r"\bИНН[\s:№#]*", re.I),               re.compile(r"\b\d{10}\b")),
    ("INN12",  re.compile(r"\bИНН[\s:№#]*", re.I),               re.compile(r"\b\d{12}\b")),
    ("OGRN",   re.compile(r"\bОГРН[\s:№#]*", re.I),              re.compile(r"\b\d{13}\b")),
    ("OGRNIP", re.compile(r"\bОГРНИП[\s:№#]*", re.I),            re.compile(r"\b\d{15}\b")),
    ("KPP",    re.compile(r"\bКПП[\s:№#]*", re.I),               re.compile(r"\b\d{9}\b")),
    ("BIK",    re.compile(r"\bБИК[\s:№#]*", re.I),               re.compile(r"\b04\d{7}\b")),
    ("RS",     re.compile(r"(?:р/?\s*с[чч]?[её]?т|расч[её]тный\s*сч[её]т|р/с)[\s:№#]*", re.I),
                                                                  re.compile(r"\b\d{20}\b")),
]

# Эти паттерны самодостаточны — формат уникален, ищем по всему тексту.
STANDALONE: list[tuple[str, re.Pattern]] = [
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    # Телефон РФ: требуем явный признак формата (+7 или 8 со скобками/дефисами),
    # иначе ловится любое 11-значное число.
    ("PHONE", re.compile(
        r"(?:\+7|\b8)[\s\-]*\(?\d{3}\)?[\s\-]\d{3}[\s\-]?\d{2}[\s\-]?\d{2}\b"
    )),
]

# ФИО: Фамилия Имя Отчество, где отчество имеет характерное окончание.
# natasha регулярно пропускает редкие фамилии (напр. "Колодийчук") — этот
# regex ловит их по окончанию отчества, не зависит от словаря имён.
FIO_PATTERN = re.compile(
    r"\b[А-ЯЁ][а-яё\-]+\s+[А-ЯЁ][а-яё\-]+\s+"
    r"[А-ЯЁ][а-яё\-]+(?:вич|ьич|ович|евич|овна|евна|ична|инична)\b"
)

# Формы собственности для regex-поиска организаций (fallback без natasha).
ORG_FORM = re.compile(
    r'(?:ООО|ОАО|ЗАО|ПАО|АО|НКО|ГК|ИП)\s+["«]?([А-ЯЁA-Z][\w\-\s.]{1,60}?)["»]?(?=[\s,.;:)\n]|$)',
    re.UNICODE,
)


def detect_regex(text: str) -> list[tuple[str, str]]:
    """
    Детектит реквизиты и emails/телефоны.
    Реквизиты с keyword-якорем — только если в пределах KEYWORD_WINDOW символов
    после ключевого слова идёт число нужного формата. Это убирает массовые
    false positives на финансовых числах.
    """
    found: list[tuple[str, str]] = []

    for kind, kw_pat, num_pat in KEYWORDED:
        for kw_m in kw_pat.finditer(text):
            window = text[kw_m.end():kw_m.end() + KEYWORD_WINDOW]
            num_m = num_pat.search(window)
            if not num_m:
                continue
            value = num_m.group(0)
            validator = VALIDATORS.get(kind)
            if validator and not validator(value):
                continue
            found.append((value, kind))

    for kind, pat in STANDALONE:
        for m in pat.finditer(text):
            found.append((m.group(0), kind))

    for m in FIO_PATTERN.finditer(text):
        found.append((m.group(0).strip(), "PER"))

    for m in ORG_FORM.finditer(text):
        candidate = m.group(0).strip()
        if _ner_keep(candidate):
            found.append((candidate, "ORG"))
    return found


# Минимальная длина для именованных сущностей. Короче — слишком много FP
# (на бухотчётности natasha теггит "ДА", "НЕТ", "РФ", "ИП" как ORG/LOC/PER).
NER_MIN_LEN = 4

# Блоклист коротких частотных слов, которые natasha регулярно тегает как
# ORG/PER/LOC на финдокументах. Дополнять по результатам прогонов.
NER_STOPWORDS = {
    "да", "нет", "рф", "ип", "ао", "ооо", "оао", "зао", "пао", "нко", "гк",
    "енс", "гк рф", "за год", "итого", "прочее", "оценочные",
    "отчисления", "накопленная", "поступления", "нематериальные",
    "нераспределенная", "за 2023 г", "за 2024 г", "за 2025 г",
}


def _ner_keep(text: str) -> bool:
    """True если NER-сущность стоит сохранять (длинная и не в стоп-листе)."""
    cleaned = text.strip()
    if len(cleaned) < NER_MIN_LEN:
        return False
    if "\n" in cleaned or "\t" in cleaned:
        return False
    if cleaned.lower() in NER_STOPWORDS:
        return False
    return True


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
        if not _ner_keep(span.text):
            continue
        if span.type == "ORG":
            # На финдокументах natasha теггит заголовки балансовых строк
            # ("Инвестиционная недвижимость", "Таможенного союза") как ORG.
            # Реальные организации ловит ORG_FORM regex (требует ООО/АО/ИП и т.п.).
            continue
        if span.type == "PER" and len(span.text.split()) < 3:
            # ФИО — это минимум Фамилия Имя Отчество. Иначе отсекаем
            # обрезки типа 'Нераспределенна', 'Оценочные'.
            continue
        if span.type in ("PER", "LOC"):
            out.append((span.text, span.type))
    return out


def detect_all(text: str, use_ner: bool = True) -> list[tuple[str, str]]:
    """Объединяет regex + (опционально) natasha NER. Дедуп — на стороне вызывающего кода."""
    result = detect_regex(text)
    if use_ner:
        result += detect_natasha(text)
    return result
