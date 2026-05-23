"""
Управление словарём замен (mapping). Один словарь на сделку — обеспечивает
консистентность псевдонимов между всеми файлами пакета продавца.

Формат:
{
  "version": 1,
  "counters": {"ORG": 3, "PER": 5, "INN10": 2, ...},
  "entries": {
    "ООО Ромашка": {"pseudonym": "ORG-001", "kind": "ORG"},
    "7712345678":  {"pseudonym": "INN-001", "kind": "INN10"},
    ...
  }
}
"""

import json
from pathlib import Path

# Префиксы псевдонимов по типу сущности.
PREFIX = {
    "ORG":    "ORG",
    "PER":    "PER",
    "LOC":    "LOC",
    "INN10":  "INN",
    "INN12":  "INN",
    "OGRN":   "OGRN",
    "OGRNIP": "OGRN",
    "KPP":    "KPP",
    "BIK":    "BIK",
    "RS":     "RS",
    "EMAIL":  "EMAIL",
    "PHONE":  "PHONE",
}


class Mapping:
    def __init__(self, path: Path):
        self.path = path
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
        else:
            data = {"version": 1, "counters": {}, "entries": {}}
        self.counters: dict[str, int] = data.get("counters", {})
        self.entries: dict[str, dict] = data.get("entries", {})
        self.files: dict[str, str] = data.get("files", {})
        self._sorted_keys: list[str] | None = None  # кэш для apply()

    def pseudonym_for(self, original: str, kind: str) -> str:
        """Возвращает существующий псевдоним или создаёт новый."""
        original = original.strip()
        if original in self.entries:
            return self.entries[original]["pseudonym"]
        prefix = PREFIX.get(kind, kind)
        self.counters[prefix] = self.counters.get(prefix, 0) + 1
        pseudonym = f"{prefix}-{self.counters[prefix]:03d}"
        self.entries[original] = {"pseudonym": pseudonym, "kind": kind}
        self._sorted_keys = None  # инвалидируем кэш
        return pseudonym

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(
                {
                    "version": 1,
                    "counters": self.counters,
                    "entries": self.entries,
                    "files": self.files,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def load_seed(self, seed_path: Path) -> int:
        """
        Загружает seed-словарь: {"оригинал": "псевдоним"} или
        {"оригинал": {"pseudonym": "...", "kind": "ORG"}}.
        Возвращает количество добавленных записей.
        """
        data = json.loads(seed_path.read_text(encoding="utf-8"))
        added = 0
        for original, value in data.items():
            if original in self.entries:
                continue
            if isinstance(value, str):
                pseudonym, kind = value, "ORG"
            else:
                pseudonym = value["pseudonym"]
                kind = value.get("kind", "ORG")
            self.entries[original] = {"pseudonym": pseudonym, "kind": kind}
            added += 1
        self._sorted_keys = None
        return added

    def apply(self, text: str) -> str:
        """
        Заменяет все известные оригиналы на псевдонимы в тексте.
        Длинные оригиналы — первыми, чтобы не съесть подстроки.
        """
        if not text:
            return text
        if self._sorted_keys is None:
            self._sorted_keys = sorted(self.entries, key=len, reverse=True)
        for original in self._sorted_keys:
            if original in text:
                text = text.replace(original, self.entries[original]["pseudonym"])
        return text
