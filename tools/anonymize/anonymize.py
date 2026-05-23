"""
CLI для анонимизации XLSX и текстовых PDF.

Использование:
    python anonymize.py <файл-или-папка> [--mapping path.json] [--out-dir dir] [--review]

Примеры:
    # одиночный файл, mapping создаётся рядом
    python anonymize.py report.xlsx

    # пакет от продавца — общий mapping на сделку
    python anonymize.py ./deal-target1/ --mapping ./deal-target1/mapping.json --out-dir ./deal-target1/anon/

    # сначала просто посмотреть что нашлось, без записи
    python anonymize.py report.xlsx --review
"""

import argparse
import sys
import tempfile
from pathlib import Path

# Windows console — переключаем stdout/stderr в UTF-8, иначе print() ломается
# на кириллице и спецсимволах (cp1251 default).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from detectors import detect_all
from handlers import process_pdf, process_xlsx
from mapping import Mapping


def anonymize_filename(src: Path, mapping: Mapping, used: set[str]) -> str:
    """
    Применяет mapping к имени файла (stem). Если в имени найдены новые сущности —
    они тоже попадают в mapping. Разрешает коллизии через суффикс -2, -3, ...
    """
    stem = src.stem
    for original, kind in detect_all(stem):
        mapping.pseudonym_for(original, kind)
    new_stem = mapping.apply(stem).strip(" _-") or "doc"
    candidate = new_stem + src.suffix.lower()
    if candidate.lower() not in used:
        used.add(candidate.lower())
        return candidate
    i = 2
    while f"{new_stem}-{i}{src.suffix.lower()}".lower() in used:
        i += 1
    candidate = f"{new_stem}-{i}{src.suffix.lower()}"
    used.add(candidate.lower())
    return candidate


SUPPORTED = {".xlsx", ".pdf"}


def collect_inputs(path: Path) -> list[Path]:
    if path.is_file():
        return [path] if path.suffix.lower() in SUPPORTED else []
    return sorted(
        p for p in path.rglob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED
    )


def output_path(src: Path, src_root: Path, out_dir: Path | None) -> Path:
    if out_dir is None:
        return src.with_name(src.stem + ".anon" + src.suffix)
    rel = src.relative_to(src_root) if src_root != src else src.name
    return out_dir / rel


def main() -> int:
    ap = argparse.ArgumentParser(description="Анонимизатор XLSX/PDF для M&A DD")
    ap.add_argument("input", type=Path, help="Файл или папка с XLSX/PDF")
    ap.add_argument("--mapping", type=Path, help="Путь к JSON-mapping (общий на сделку)")
    ap.add_argument("--out-dir", type=Path, help="Папка для анонимизированных файлов")
    ap.add_argument("--review", action="store_true",
                    help="Только показать найденные сущности, без записи файлов")
    ap.add_argument("--rename", action="store_true",
                    help="Анонимизировать также имена файлов (использует mapping)")
    ap.add_argument("--no-ner", action="store_true",
                    help="Отключить natasha NER (быстрее, но не найдёт ФИО/орг без формы)")
    args = ap.parse_args()

    if not args.input.exists():
        print(f"ERROR: {args.input} не найден", file=sys.stderr)
        return 2

    inputs = collect_inputs(args.input)
    if not inputs:
        print(f"ERROR: не найдено .xlsx/.pdf в {args.input}", file=sys.stderr)
        return 2

    src_root = args.input if args.input.is_dir() else args.input.parent
    mapping_path = args.mapping or (src_root / "mapping.json")
    mapping = Mapping(mapping_path)

    print(f"Mapping: {mapping_path} ({len(mapping.entries)} существующих записей)")
    print(f"Файлов к обработке: {len(inputs)}")
    print()

    tmp_dir = Path(tempfile.mkdtemp(prefix="anon-review-")) if args.review else None
    used_names: set[str] = {v.lower() for v in mapping.files.values()}
    use_ner = not args.no_ner
    import time

    for src in inputs:
        suffix = src.suffix.lower()
        if args.review:
            dst = tmp_dir / (src.stem + ".tmp" + suffix)
        else:
            dst = output_path(src, src_root, args.out_dir)
        t0 = time.time()
        print(f"  {src.name} ...", flush=True)
        try:
            if suffix == ".xlsx":
                stats = process_xlsx(src, dst, mapping, use_ner=use_ner)
            elif suffix == ".pdf":
                stats = process_pdf(src, dst, mapping, use_ner=use_ner)
            else:
                continue
            stats["sec"] = round(time.time() - t0, 1)

            # Переименование после обработки содержимого: mapping уже полный для этого файла
            final_dst = dst
            if args.rename and not args.review:
                new_name = anonymize_filename(src, mapping, used_names)
                if new_name != dst.name:
                    final_dst = dst.with_name(new_name)
                    dst.replace(final_dst)
                mapping.files[src.name] = final_dst.name

            arrow = "→ (review)" if args.review else f"→ {final_dst}"
            print(f"  {src.name} {arrow}")
            print(f"    {stats}")
        except Exception as e:
            print(f"  {src.name} FAILED: {e}", file=sys.stderr)

    if tmp_dir:
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)

    mapping.save()
    print()
    print(f"Mapping сохранён: {mapping_path}")
    print(f"Всего сущностей в mapping: {len(mapping.entries)}")
    print()
    print("ВАЖНО: mapping.json — это ключ деанонимизации. Храни локально, не загружай в Claude.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
