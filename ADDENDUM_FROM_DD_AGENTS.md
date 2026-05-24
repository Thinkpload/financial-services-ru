# Addendum — заимствования из zoharbabin/dd-agents

Источник: [github.com/zoharbabin/due-diligence-agents](https://github.com/zoharbabin/due-diligence-agents) (Apache 2.0, на том же `claude-agent-sdk`, что и наши Managed Agent cookbooks). Это **отдельный** документ — не диффит [RU_ADAPTATION_PLAN.md](RU_ADAPTATION_PLAN.md), чтобы не пересекаться с уже идущей реализацией первого плана. Применяется ПОСЛЕ того, как базовый план дойдёт до пилота.

Контекст сравнения и почему смотрим — см. историю обсуждения; коротко: у них западный mid-market DD, у нас РФ-микро-ИТ-аутсорс. Пересечения архитектурные, не доменные.

## Приоритет внедрения

| # | Блок | Куда встаёт | Когда |
|---|------|-------------|-------|
| 1 | Red-flag scanner (РФ-категории) | новый P-1, до P0 whitening | сразу после пилота |
| 2 | `numerical_manifest.json` | артефакт P0 whitening | в ходе P0, обязательный |
| 3 | Judge agent | между P6 и P7 | после стабилизации P0–P6 |
| 4 | Chronicle (per-deal + portfolio) | сквозной слой | после 3+ закрытых сделок |
| 5 | markitdown + динамический SDK-буфер | extraction | при первой xlsx-выгрузке 1С >5MB |
| 6 | Бюджеты в каждом `agent.yaml` | все cookbooks | при следующем рефреше cookbooks |

Пункт «lineage.json» сознательно опущен — у нас один прогон до пилотного решения, многократные прогоны одной сделки не предусмотрены DoD.

---

## 1. P-1 — Red-Flag Quick-Scan (РФ-категории)

**Цель:** GREEN/YELLOW/RED за минуты до запуска полного пайплайна. Отсечь явно нерабочие таргеты до P0.

**Архитектура (из `red_flag_scanner.py`):** single-turn агент, инструменты только `Read/Glob/Grep`, выход — структурированный `RedFlagScannerOutput` (`overall_signal`, `recommendation`, `flags[]`).

**Логика свёртки сигнала:**
- любой P0 → `red`
- P1 + confidence=high → `red`
- P1 + medium/low → `yellow`
- P2 → `yellow`
- иначе → `green`

**8 РФ-категорий (заменяют западные active_litigation/MFN/SOC2):**

1. `ip_employees_signals` — ИП-«сотрудники», признаки трудовых отношений (массовые ИП на УСН 6%, одинаковые ОКВЭД, регистрация близко по дате к найму).
2. `usn_splitting` — дробление: несколько связанных ЮЛ/ИП <150 млн ₽ выручки, общие учредители/директора/адрес/IP-логи.
3. `cash_envelope_gap` — разрыв между банковскими оборотами и официальной выручкой, признаки «конверта».
4. `assets_on_owner` — лицензии / домены / репозитории / договоры с ключевыми клиентами оформлены на физлицо собственника, не на ЮЛ сделки.
5. `client_concentration` — >30% выручки на одного клиента; change-of-control пункты в их договорах.
6. `it_accreditation_gap` — заявлены ИТ-льготы, но нет/отозвана аккредитация Минцифры, не выполняются критерии (доля ИТ-выручки, средняя ЗП).
7. `tax_debt_signals` — публичная задолженность ФНС, блокировки счёта, открытые требования, признаки спорных доначислений.
8. `founder_dependency` — выручка/клиенты/найм/код завязаны на собственнике; 4 сценария «бизнес без него» проваливаются.

**Бюджет:** `max_turns=30`, `max_budget_usd=0.50`. Это дешёвый отсев, не анализ.

**Выход:** `deals/<target>/quickscan.json` + однострочная рекомендация в [PORTRAIT.md](PIPELINE_SCHEMA.md) frontmatter.

---

## 2. `numerical_manifest.json` — обязательный артефакт P0 whitening

**Зачем:** продавец будет спорить за каждую корректировку EBITDA. Без traceability «методология» — слабая позиция; с traceability спор сводится к конкретным строкам.

**Схема (адаптация `models/numerical.py`):**

```python
class WhiteningManifestEntry(BaseModel):
    id: str                              # W001, W002, ...
    label: str                           # "salary_ip_to_white_fot"
    value_seller: float                  # как у продавца
    value_white: float                   # пересчёт в белую
    delta: float                         # value_white - value_seller
    source_file: str                     # путь в data_room
    derivation: str                      # формула/метод
    used_in: list[str]                   # в каких MD-секциях встречается
    cross_check: str                     # независимая проверка (банк vs 1С vs справки)
    verified: bool
    whitening_adjustment: bool           # это корректировка whitening или базовый факт?
    tier_evidence: Literal["T1","T2","T3"]  # LLM / аналитик / эксперт
    confidence: Literal["high","medium","low"]
```

**Минимум:** ≥30 записей (их потолок «≥10» под mid-market; для микро-ИТ-аутсорса критичных корректировок намного больше: ФОТ→белый ФОТ, аренда на собственнике→market rate, лицензии, страховые, НДФЛ, НДС-разрывы, налог на УСН vs ОСНО и т.д.).

**Локация:** `deals/<target>/numerical_manifest.json`.

**Правило:** ни одна цифра в `PORTRAIT.md` и 8 секциях не появляется без записи в manifest. Это инвариант пайплайна, проверяется gates.

---

## 3. Judge agent — quality-gate между P6 и P7

**Из `agents/judge.py` дословно полезно:**

- **Risk-based sampling** (не ревьюим всё, дорого): P0=100%, P1=20%, P2=10%, P3=0%.
- **Iteration loop:** если score < threshold → таргетный re-spawn упавшего агента, до 2 раундов. Финальный = `0.7·новый + 0.3·прежний`.
- **Бюджет:** `max_turns=150`, `max_budget_usd=3.0`.

**Адаптация измерений под нас (6 вместо 5):**

| Dimension | Вес | Что проверяет |
|-----------|-----|---------------|
| `citation_verification` | 0.25 | все цифры/факты привязаны к источнику в data_room |
| `whitening_accuracy` | 0.25 | корректировки EBITDA сходятся с numerical_manifest, нет двойного счёта |
| `russian_jurisdiction_fit` | 0.15 | 152-ФЗ / ИТ-аккр / УСН-сигналы не перепутаны с US-аналогами |
| `contextual_validation` | 0.15 | находки соответствуют отраслевой норме для МСБ ИТ-аутсорса |
| `cross_agent_consistency` | 0.10 | tax-risk не противоречит whitening, IT-аккр не противоречит финмодели |
| `completeness` | 0.10 | покрыты все 10 смысловых слоёв из брифа |

**Threshold:** общий 70/100; для секций с whitening_adjustment — 80/100 (выше цена ошибки).

**Локация:** `agent-plugins/ru-dd-judge/` + cookbook `managed-agent-cookbooks/ru-dd-judge/`.

---

## 4. Chronicle — per-deal + portfolio

**Из `knowledge/chronicle.py`:** append-only JSONL, атомарная запись через tempfile + `os.replace`.

**Наша адаптация — два уровня, не один:**

### 4a. `deals/<target>/chronicle.jsonl` — per-deal audit trail

Типы событий: `pipeline_run | quickscan | whitening_recalc | seller_followup_sent | tier_escalation | analyst_annotation | expert_review`.

Назначение: восстановить, в каком состоянии были выводы на момент переговоров с продавцом / решения LOI.

### 4b. `portfolio/chronicle.jsonl` — cross-deal benchmarks

То, ради чего вообще нужна фиксированная схема: после 5–7 закрытых сделок появляются эмпирические распределения:

- «типичная whitening-дельта EBITDA для микро-ИТ-аутсорса: 35–55%»
- «у 4 из 7 ИП-схем тот же tax-risk-сигнатура»
- «среднее число клиентов с >30% долей: 1.2»

Эти бенчмарки автоматически инжектятся как context в P-1 quickscan следующей сделки.

**Локация:** `portfolio/` — новый каталог, sibling к `deals/`.

---

## 5. Extraction — markitdown + динамический буфер SDK

**markitdown** (`markitdown[docx,pptx,xlsx]>=0.1`): нормализация офисных файлов в MD. Сейчас у нас этот слой не описан — продавцы шлют .xlsx-выгрузки 1С, .docx-договоры, .pptx-презентации; нужен единый pre-step.

**Динамический буфер SDK (из `base.py`):**

```python
buffer_bytes = clamp(largest_extracted_file_size * 1.5, 5*MB, 25*MB)
```

Без этого 1С-выгрузка на 8 МБ обрезается, и P0 whitening считает не по полным данным.

**Локация:** новый скилл `vertical-plugins/ru-it-outsource-dd/skills/ru-document-normalize/` + `tools/normalize/` в соседнем pipeline-репо.

---

## 6. Бюджеты в каждом `agent.yaml`

Сейчас в наших cookbooks потолки не выставлены явно. Из их `base.py`:

```yaml
limits:
  max_turns: 200           # default; quickscan=30, judge=150
  max_budget_usd: 5.0      # default; quickscan=0.50, judge=3.0
  hard_limit_multiplier: 3 # принудительная отмена при max_turns*3
  max_subjects_per_batch: 20
  max_tokens_per_batch: 40000
```

Применить ко всем cookbooks в `managed-agent-cookbooks/` при следующем рефреше. Это страховка от runaway-стоимости при ошибочной конфигурации.

---

## Что НЕ берём и почему

- **`knowledge/lineage.py`** — отслеживание эволюции находок между прогонами одной сделки. У нас DoD = один прогон до пилотного решения, многократные не предусмотрены.
- **9 западных доменов** (ESG, антитраст, NOL, MFN, SOC2/ISO27001) — не наш сегмент, размоет фокус.
- **HTML-репорт + Excel pipeline** — у нас сознательный выбор MD + outbound PDF продавцу.
- **ChromaDB / векторный поиск** — для 10–30 сделок/год grep по MD хватит; добавим, когда упрёмся.
- **pip-package / Docker / Homebrew Formula** — не SaaS, явно в брифе.

---

## Open questions для обсуждения перед внедрением

1. **Portfolio chronicle:** хранить рядом с `deals/` в этом же репо или вынести в отдельный private-репо (бенчмарки = чувствительный актив)?
2. **Judge:** запускать на каждом прогоне или только перед эскалацией в Tier 2/3 (дешевле, но теряем gate на Tier 1)?
3. **Quickscan:** автономный плагин или часть `ru-it-outsource-dd`? Если он по сути «фильтр воронки», может жить как `vertical-plugins/ru-it-outsource-quickscan/` — отдельный продукт.
4. **Numerical manifest:** генерируется в P0 одним скиллом или каждый whitening-скилл аппендит свои записи? Второе масштабируется лучше, но требует locking при параллельных агентах.
