"""Spike: overlay one entity replacement on a real PDF using PyMuPDF."""
import sys
from pathlib import Path
import fitz

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "test-data" / "Бухгалтерская отчетность за 2025\xa0г. (ИНФОТЕХ СЕРВИС, ООО).pdf"
DST = ROOT / "test-data" / "_spike_overlay.pdf"
NEEDLE = "ИНФОТЕХ СЕРВИС"
REPLACEMENT = "TARGET-A"
FONT_PATH = r"C:\Windows\Fonts\arial.ttf"


def main() -> int:
    if not SRC.exists():
        print(f"missing: {SRC}", file=sys.stderr)
        return 1

    doc = fitz.open(SRC)
    total_hits = 0
    for page in doc:
        rects = page.search_for(NEEDLE)
        total_hits += len(rects)
        for rect in rects:
            page.add_redact_annot(rect, fill=(1, 1, 1))
        page.apply_redactions()
        for rect in rects:
            font_size = max(6.0, rect.height * 0.8)
            page.insert_textbox(
                rect,
                REPLACEMENT,
                fontname="overlay",
                fontfile=FONT_PATH,
                fontsize=font_size,
                color=(0, 0, 0),
                align=0,
            )
    doc.save(DST, deflate=True)
    doc.close()

    verify = fitz.open(DST)
    leaked = sum(len(p.search_for(NEEDLE)) for p in verify)
    verify.close()

    print(f"hits replaced: {total_hits}")
    print(f"leaked after: {leaked}")
    print(f"output: {DST}")
    return 0 if leaked == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
