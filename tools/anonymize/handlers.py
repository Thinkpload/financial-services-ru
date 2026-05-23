"""
Обработчики форматов: XLSX и текстовый PDF.

Стратегия:
- XLSX: openpyxl, обход ячеек, замена только строковых значений.
  Числа и формулы не трогаем (финданные должны остаться валидными).
  Заголовки/комментарии/имена листов — анонимизируются.
- PDF: pdfplumber извлекает текст постранично → mapping.apply → reportlab
  пересобирает простой текстовый PDF. Лейаут теряется, содержимое сохраняется.
  Для финдокументов это приемлемо: для расчётов всё равно используем XLSX-источник.
"""

from pathlib import Path

import openpyxl
import pdfplumber
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from detectors import detect_all
from mapping import Mapping


# --- XLSX ---------------------------------------------------------------------

def process_xlsx(src: Path, dst: Path, mapping: Mapping) -> dict:
    wb = openpyxl.load_workbook(src, data_only=False)
    stats = {"cells_scanned": 0, "cells_changed": 0, "new_entities": 0}
    before = len(mapping.entries)

    # Имена листов тоже анонимизируем
    for sheet in wb.worksheets:
        for row in sheet.iter_rows():
            for cell in row:
                if cell.value is None or not isinstance(cell.value, str):
                    continue
                stats["cells_scanned"] += 1
                text = cell.value
                # Детектим новые сущности в этой ячейке
                for original, kind in detect_all(text):
                    mapping.pseudonym_for(original, kind)
                # Применяем все известные замены
                new_text = mapping.apply(text)
                if new_text != text:
                    cell.value = new_text
                    stats["cells_changed"] += 1

    # Имена листов
    for sheet in wb.worksheets:
        new_title = mapping.apply(sheet.title)
        if new_title != sheet.title:
            sheet.title = new_title[:31]  # лимит Excel

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

def _register_cyrillic_font() -> str:
    """Регистрирует кириллический TTF из системы Windows. Возвращает имя шрифта."""
    candidates = [
        ("DejaVuSansMono", "C:/Windows/Fonts/consola.ttf"),
        ("DejaVuSansMono", "C:/Windows/Fonts/cour.ttf"),
        ("DejaVuSansMono", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"),
    ]
    for name, path in candidates:
        if Path(path).exists():
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                return name
            except Exception:
                continue
    return "Helvetica"  # последний fallback, кириллица сломается


def process_pdf(src: Path, dst: Path, mapping: Mapping) -> dict:
    stats = {"pages": 0, "chars_in": 0, "new_entities": 0}
    before = len(mapping.entries)

    pages_text: list[str] = []
    with pdfplumber.open(src) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            stats["chars_in"] += len(text)
            stats["pages"] += 1
            # Детектим новые сущности постранично
            for original, kind in detect_all(text):
                mapping.pseudonym_for(original, kind)
            pages_text.append(text)

    # Применяем замены ко всем страницам уже после полного сбора mapping
    pages_anon = [mapping.apply(t) for t in pages_text]

    # Пересобираем PDF
    dst.parent.mkdir(parents=True, exist_ok=True)
    font = _register_cyrillic_font()
    c = canvas.Canvas(str(dst), pagesize=A4)
    width, height = A4
    margin = 40
    line_height = 11
    font_size = 9
    max_lines = int((height - 2 * margin) / line_height)
    max_chars = int((width - 2 * margin) / (font_size * 0.55))  # грубая оценка

    for page_text in pages_anon:
        lines: list[str] = []
        for raw in page_text.splitlines():
            if not raw:
                lines.append("")
                continue
            while len(raw) > max_chars:
                lines.append(raw[:max_chars])
                raw = raw[max_chars:]
            lines.append(raw)

        # Разбиваем на страницы PDF по max_lines
        for i in range(0, max(len(lines), 1), max_lines):
            chunk = lines[i:i + max_lines]
            c.setFont(font, font_size)
            y = height - margin
            for line in chunk:
                c.drawString(margin, y, line)
                y -= line_height
            c.showPage()

    c.save()
    stats["new_entities"] = len(mapping.entries) - before
    return stats
