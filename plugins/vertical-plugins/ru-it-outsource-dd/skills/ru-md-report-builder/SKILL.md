---
name: ru-md-report-builder
description: Final Markdown report builder for a single deal — aggregates outputs from all P0-P5 skills into 8 standardized sections (summary, whitening, financial, tax-risks, IT-accreditation, 152-FZ, legal-SPA, people) plus a machine-aggregatable PORTRAIT.md with frontmatter. Stable headers, GFM tables, YAML frontmatter per section. Used by P6.7 (outbound pack) and for cross-deal portfolio analysis. Triggers on "md report", "финальный отчёт", "PORTRAIT.md", "собрать отчёт", "8 секций".
---

# MD Report Builder (P6)

Финальная склейка пайплайна. Собирает MD-отчёт по сделке + машинно-агрегируемый `PORTRAIT.md` для cross-deal анализа.

**Принцип:** ничего не вычисляет. Только агрегирует выходы P0-P5 в стабильный формат.

## When to use

- Завершены минимум: P0.5, P0, P1, P5 (для скрининга достаточно)
- Завершены желательно: P1.5, P1.7, P1.8, P2, P2.5, P2.7, P2.8, P3, P4 (для полного отчёта)
- Запускается после каждого крупного обновления входов (новый документ от продавца → re-run)

## Inputs

- Все frontmatter блоки от P0-P5 (yaml объекты по контракту в [PIPELINE_SCHEMA.md](../../../../../PIPELINE_SCHEMA.md))
- Анонимайзер mapping для деанонимизации (только для internal версии)
- Шаблоны секций (08-section templates)

## Workflow

### Step 1: Файловая структура

```
deals/<target-slug>/
  raw/                          # оригиналы от продавца (gitignored)
  anon/                         # анонимизированные (выход анонимайзера)
  mapping.json                  # ключ деанонимизации (gitignored)
  external/
    rusprofile/                 # из P0.7
  whitened/
    finmodel_whitened.xlsx      # из P0 Step 6
  reports/
    01-summary.md               # 1 экран
    02-whitening.md             # whitening adjustment + сценарии
    02b-multi-entity.md         # multi-entity recon
    03-financial.md             # RSBU audit + working capital
    03a-by-direction.md         # P1.5
    03b-recurring.md            # client base recurring split
    04-tax-risks.md             # P1
    05-it-accreditation.md      # P2
    06-152fz.md                 # P3
    07-legal-spa.md             # P4
    08-people.md                # P2.7 owner-dep + key people
    09-assets.md                # P2.8
    PORTRAIT.md                 # машинно-агрегируемая выжимка
    checklist.md                # P-checklist (живой документ)
    chronicle.jsonl             # append-only audit trail (см. Addendum 4a)
```

### Step 2: 01-summary.md (1 экран)

Структура:
```markdown
---
target_slug: TARGET-A
inn_pseudonym: INN-001
report_date: 2026-05-24
report_version: v3
recommendation: rework_price | proceed | escalate | walk_away
escalation_tier: 1 | 2 | 3
---

# Summary — <target>

## Рекомендация
[1 строка: rework_price to ~34M / proceed at asking / walk_away — main reason]

## Топ-цифры
| Метрика | Значение |
|---|---|
| Asking price | … |
| Implied price (на whitened EBITDA) | … |
| Price gap | … |
| Whitening gap | …% |
| Tax-risk reserve (base) | … |
| Total indemnity proposed | … |
| Revenue at CoC risk | …% |

## Топ-5 red flags
1. [high] (impact 14.8M ₽) — Tax-risk: дробление + 54.1 + конверты
2. [high] (impact 12M ₽) — CoC: TARGET-A теряет 3 топ-клиента при смене бенефициара
3. ...

## Next steps
- [ ] Запросить недостающее (см. checklist.md, осталось N пунктов)
- [ ] Звонок с продавцом по open_questions (см. 08-people.md)
- [ ] Tier 2/3 review по тем-то блокам
```

### Step 3: 02-09 секции

Каждая секция:
- Frontmatter — структурированный блок от соответствующего скилла
- Body — MD из output этого скилла
- В конце — «Связи с другими секциями» с явными cross-refs

### Step 4: PORTRAIT.md

Только frontmatter + ссылки на источники. Тело почти пустое (1-2 ссылки на 01-summary).

```yaml
---
target_slug: TARGET-A
report_date: 2026-05-24
deal_stage: dd
group:                                # из P0.5
  entities_in_deal: 2
  entities_in_group: 3
financials:                           # из P0 + P5
  revenue_2024_rub: ...
  ebitda_reported_rub: ...
  ebitda_white_baseline_rub: ...
  whitening_gap_pct: ...
valuation:                            # из P1.7
  asking_price_rub: ...
  implied_price_white_base_rub: ...
  price_gap_pct: ...
tax_risk:                             # из P1
  total_base_rub: ...
client_base:                          # из P1.8
  top3_share_pct: ...
  recurring_share_pct: ...
  coc_risk_revenue_pct: ...
it_accreditation:                     # из P2
  sustainability: ...
  benefit_5yr_rub: ...
compliance:                           # из P3
  fine_potential_base_rub: ...
  kii_blocker: ...
owner_dependency:                     # из P2.7
  weighted_ebitda_after_rub: ...
assets:                               # из P2.8
  one_time_transfer_cost_rub: ...
spa:                                  # из P4
  indemnity_cap_rub: ...
  escrow_rub: ...
reliability:                          # из P5
  overall: ...
recommendation:                       # из P7
  tier: ...
  action: ...
---

См. [01-summary.md](01-summary.md).
```

Все ключевые цифры **из frontmatter других секций** — не пересчитываются здесь. Это инвариант.

### Step 5: Cross-deal analytics

PORTRAIT.md → можно делать grep/jq по портфелю:
```bash
# Все сделки где whitening_gap > 40%
find deals/ -name PORTRAIT.md | xargs grep -l "whitening_gap_pct: 4[0-9]\|whitening_gap_pct: [5-9][0-9]"

# Все сделки с КИИ-блокерами
find deals/ -name PORTRAIT.md | xargs grep -l "kii_blocker: true"
```

После 5+ сделок — портфельные бенчмарки (Addendum 4b).

### Step 6: Format requirements

1. **Стабильные заголовки H2** — критично для извлечения секций LLM-агентом
2. **Frontmatter в YAML** в каждой секции — структурированные факты для машинной обработки
3. **Числа без форматирования** (`1234567` not `1 234 567 ₽`)
4. **Цитаты — blockquote с указанием source файла**
5. **Red flags формат:** `- [severity] (impact_rub) описание (ссылка на секцию)`
6. **Cross-refs:** `[01-summary.md#topcifry](01-summary.md)` style

## Output contract

Producer финальной структуры `deals/<target>/reports/`. Consumers: P6.7 (outbound pack берёт sections из 01/03a/03b/08), P7 (читает PORTRAIT.md frontmatter для routing), внешние pipeline / agents.

## Failure modes & guardrails

- **Не считать здесь ничего.** Если значение нужно в summary — оно должно прийти из frontmatter другого скилла. Иначе подгонка.
- **Если секция blocked** (входящий скилл не отработал) — placeholder с явным указанием, не пустой раздел.
- **Версионирование:** `report_version` инкрементируется при каждом re-run. Старые версии не удаляются автоматически (git history достаточно).
- **Чувствительные данные:** internal версия с реальными именами клиентов — отдельный артефакт, gitignored. Коммитится только anonymized версия.

## Опциональный второй проход (отдельные скиллы, НЕ часть P6)

- MD → HTML с Chart.js для презентации партнёрам
- MD → PDF через pandoc для подписи / архива  (P6.7 использует это для outbound)
- MD → инфографика на запрос

## Связанные скиллы

- **Prerequisites:** все P0-P5
- **Downstream:** P6.7 (outbound pack), P7 (routing)
