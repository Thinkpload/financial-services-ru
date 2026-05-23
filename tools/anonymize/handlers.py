"""
Обработчики форматов: XLSX и PDF.

Стратегия:
- XLSX: openpyxl, обход ячеек, замена только строковых значений.
  Числа и формулы не трогаем (финданные должны остаться валидными).
  Заголовки/комментарии/имена листов — анонимизируются.
- PDF: PyMuPDF (fitz) overlay — поверх оригинала. Для каждой сущности из
  mapping ищем bbox через page.search_for(), редактируем
  (add_redact_annot + apply_redactions стирают текстовый слой под прямоугольником),
  и впечатываем псевдоним тем же кеглем. Вёрстка/таблицы/печати сохраняются.
"""

import sys
from pathlib import Path

import fitz
import openpyxl

from detectors import detect_all
from mapping import Mapping


# --- XLSX ---------------------------------------------------------------------

def process_xlsx(src: Path, dst: Path, mapping: Mapping, use_ner: bool = True) -> dict:
    wb = openpyxl.load_workbook(src, data_only=False)
    stats = {"cells_scanned": 0, "cells_changed": 0, "new_entities": 0}
    before = len(mapping.entries)

    # Pass 1: собираем строковые значения и гоняем детекторы чанками.
    # Большие книги (>1M символов) рвут natasha по памяти если делать одним blob —
    # её embedding строит матрицу O(n²) и улетает в OOM на 2-4 ГБ.
    parts: list[str] = []
    for sheet in wb.worksheets:
        parts.append(sheet.title)
        for row in sheet.iter_rows(values_only=True):
            for v in row:
                if isinstance(v, str) and v:
                    parts.append(v)

    NER_CHUNK = 200_000  # символов — эмпирически безопасно для natasha на 16 ГБ RAM
    chunks: list[str] = []
    buf: list[str] = []
    buf_len = 0
    for p in parts:
        if buf_len + len(p) > NER_CHUNK and buf:
            chunks.append("\n".join(buf))
            buf, buf_len = [], 0
        buf.append(p)
        buf_len += len(p) + 1
    if buf:
        chunks.append("\n".join(buf))

    # На больших книгах natasha иногда падает с OOM даже после чанковки
    # (зависит от плотности именованных сущностей в чанке). При любом сбое
    # детектора переключаемся на regex-only для оставшихся чанков и логируем.
    ner_active = use_ner
    for chunk in chunks:
        try:
            entities = detect_all(chunk, use_ner=ner_active)
        except (MemoryError, Exception) as e:
            if not ner_active:
                raise
            print(
                f"    WARN: natasha NER failed on {src.name} ({type(e).__name__}: {e}), "
                f"продолжаю без NER (regex-only)",
                file=sys.stderr,
            )
            ner_active = False
            entities = detect_all(chunk, use_ner=False)
            stats["ner_fallback"] = True
        for original, kind in entities:
            mapping.pseudonym_for(original, kind)

    # Pass 2: применяем mapping к каждой ячейке (быстрый regex-replace, без NER).
    for sheet in wb.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                if cell.value is None or not isinstance(cell.value, str):
                    continue
                stats["cells_scanned"] += 1
                new_text = mapping.apply(cell.value)
                if new_text != cell.value:
                    cell.value = new_text
                    stats["cells_changed"] += 1
        new_title = mapping.apply(sheet.title)
        if new_title != sheet.title:
            sheet.title = new_title[:31]

    # Очистка метаданных
    props = wb.properties
    props.creator = "anonymized"
    props.lastModifiedBy = "anonymized"
    props.title = None
    props.subject = None
    props.description = None
    props.keywords = None
    props.company = None

    dst.parent.mkdir(parents=True, exist_ok=True)
    wb.save(dst)
    stats["new_entities"] = len(mapping.entries) - before
    return stats


# --- PDF ----------------------------------------------------------------------

def _cyrillic_font_path() -> str | None:
    """Путь к кириллическому TTF. None если не нашли — текст overlay будет битый."""
    for path in (
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/consola.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        if Path(path).exists():
            return path
    return None


def process_pdf(src: Path, dst: Path, mapping: Mapping, use_ner: bool = True) -> dict:
    stats = {"pages": 0, "chars_in": 0, "new_entities": 0,
             "replacements": 0, "leaks": 0}
    before = len(mapping.entries)
    font_path = _cyrillic_font_path()

    doc = fitz.open(src)

    # Pass 1: собрать весь текст, прогнать детекторы — пополнить mapping.
    pages_text: list[str] = []
    for page in doc:
        text = page.get_text() or ""
        stats["chars_in"] += len(text)
        stats["pages"] += 1
        pages_text.append(text)
    for original, kind in detect_all("\n".join(pages_text), use_ner=use_ner):
        mapping.pseudonym_for(original, kind)

    # Pass 2: для каждой страницы — найти bbox всех сущностей, редактировать,
    # вписать псевдонимы. Длинные ключи первыми чтобы не съедало подстроки.
    keys_sorted = sorted(mapping.entries, key=len, reverse=True)
    for page_num, page in enumerate(doc, 1):
        matches: list[tuple[fitz.Rect, str]] = []
        claimed: list[fitz.Rect] = []
        for key in keys_sorted:
            rects = page.search_for(key)
            if not rects:
                continue
            pseudonym = mapping.entries[key]["pseudonym"]
            for rect in rects:
                # Пропускаем bbox, который существенно пересекается с уже занятым
                # более длинным ключом: иначе на одном куске текста окажется
                # два псевдонима друг поверх друга.
                overlaps = False
                for c in claimed:
                    inter = rect & c
                    if not inter.is_empty and inter.get_area() > 0.5 * rect.get_area():
                        overlaps = True
                        break
                if overlaps:
                    continue
                claimed.append(rect)
                matches.append((rect, pseudonym))

        if not matches:
            continue

        for rect, _ in matches:
            page.add_redact_annot(rect, fill=(1, 1, 1))
        page.apply_redactions()

        for rect, pseudonym in matches:
            font_size = max(5.0, rect.height * 0.85)
            # insert_textbox возвращает отрицательное число при переполнении —
            # пробуем уменьшать шрифт до 4pt, дальше просто пишем как есть.
            kwargs = {
                "fontsize": font_size, "color": (0, 0, 0), "align": 0,
            }
            if font_path:
                kwargs["fontname"] = "overlay"
                kwargs["fontfile"] = font_path
            else:
                kwargs["fontname"] = "helv"
            while font_size >= 4.0:
                kwargs["fontsize"] = font_size
                rc = page.insert_textbox(rect, pseudonym, **kwargs)
                if rc >= 0:
                    break
                font_size -= 0.5
            stats["replacements"] += 1

    dst.parent.mkdir(parents=True, exist_ok=True)
    doc.save(dst, deflate=True, garbage=4)
    doc.close()

    # Контроль: открыть результат, прогнать поиск по всем ключам,
    # залогировать всё что осталось (без падения и без отката).
    verify = fitz.open(dst)
    for page_num, page in enumerate(verify, 1):
        for key in keys_sorted:
            if page.search_for(key):
                stats["leaks"] += 1
                print(
                    f"    WARN: leak '{key[:60]}' on page {page_num} of {src.name}",
                    file=sys.stderr,
                )
    verify.close()

    stats["new_entities"] = len(mapping.entries) - before
    return stats
