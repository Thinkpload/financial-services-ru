---
name: ru-owner-dependency-model
description: Model the founder/owner as two separate line items — cash extraction (how much they take out) and operational role (what they actually do day-to-day) — then estimate replaceability cost and run 4 scenarios for "business without founder" (A stable / B replacements needed / C economics worsens / D model collapses). Critical for IT-outsourcing MSB where founder typically runs both sales and top-tier delivery. Triggers on "owner dependency", "зависимость от собственника", "founder risk", "replaceability", "что делает собственник", "без founder".
---

# Owner Dependency Model (P2.7)

В МСБ ИТ-аутсорсе собственник почти всегда выполняет 2-3 разные функции одновременно: главный продавец, главный архитектор/решатель проблем, ключевой контакт топ-клиентов, операционный директор. **При выходе из бизнеса (типично 6-18 месяцев после сделки) эти функции теряются одновременно.** Generic «key person risk» из апстрима этого не покрывает.

Скилл моделирует собственника **как 2 статьи**: деньги и функции. Затем — «бизнес без него» в 4 сценариях.

## When to use

- Завершён P1.5 (cash extraction отделён от прочих расходов)
- Завершён P0 (есть post-deal EBITDA baseline)
- Завершён P1.8 (известно, на каких клиентах сидит собственник лично)
- Перед IC-memo и SPA (retention bonus + earn-out conditions зависят от модели)

## Inputs

- Cash extraction по собственнику (P1.5): ЗП + дивиденды + выплаты на связанное ИП собственника + неформальные изъятия
- Список функций собственника: продажи / архитектура / поддержка топ-клиентов / операционка / финансы (по интервью или DD-вопросам)
- Клиенты с прямой owner-relationship (из P1.8)
- Региональные ставки замещающих ролей: коммерческий директор, тимлид, тех.директор

## Workflow

### Step 1: Cash extraction (статья 1)

Из P1.5 — все потоки на собственника:

```yaml
owner_cash_extraction:
  salary_official_rub: 1800000
  dividends_rub: 4200000
  payments_to_related_ip_rub: 6000000
  estimated_cash_envelopes_rub: 1500000   # косвенно
  total_annual_rub: 13500000
```

Это **не» расход бизнеса в полном смысле — после сделки часть нормализуется (становится зарплатой наёмному CEO/директору), часть исчезает. **Размер этой статьи — потолок «дисконта» к whitening, не больше.**

### Step 2: Operational role (статья 2)

Каталогизировать функции:

| Функция | % времени собственника | Критичность для выручки | Replaceability |
|---|---|---|---|
| Sales (top-клиенты, новые сделки) | 30% | high (≥20% выручки) | hard — нужен sales-director |
| Архитектура / решение тех.проблем | 25% | high (стабильность сервиса) | medium — senior engineer |
| Owner relationships (топ-3 клиента) | 15% | catastrophic (>40% выручки) | very hard — личные связи |
| Операционка / процессы | 20% | medium | easy — operations manager |
| Финансы / банк / налоги | 10% | low (можно отдать на аутсорс) | easy |

### Step 3: Replaceability cost

Для каждой функции — **сколько стоит заменить**:

```yaml
replacement_plan:
  - function: sales
    role_needed: "Commercial Director"
    annual_cost_rub: 4800000        # white salary + insurance
    onboarding_months: 6
    revenue_at_risk_during_transition_rub: 8000000
  - function: architecture
    role_needed: "Senior Engineer / Tech Lead"
    annual_cost_rub: 3600000
    onboarding_months: 3
  - function: top_client_owner_relationship
    role_needed: "Account Manager + retention bonus to owner"
    annual_cost_rub: 1800000
    plus_retention_bonus_to_seller_rub: 5000000   # one-time, через SPA
    risk_residual: high
```

Сумма `annual_cost_total` идёт как **дополнительный расход** в post-deal EBITDA Сценарий C (см. ниже).

### Step 4: 4 сценария «бизнес без основателя»

```yaml
scenarios:
  A_stable:
    description: "Все функции воспроизводимы, retention key clients ок"
    additional_cost_annual_rub: 6400000     # только operations
    revenue_impact_pct: 0
    probability_estimate: 0.20
    ebitda_after_rub: <P0 baseline − A_cost>
  B_replacements_needed:
    description: "Нужно нанимать 2-3 топ-роли, переходный период"
    additional_cost_annual_rub: 10200000
    revenue_impact_pct: -10                 # потеря части new sales
    probability_estimate: 0.45
    ebitda_after_rub: ...
  C_economics_worsens:
    description: "Потеря 1-2 топ-клиентов на owner-relationship, маржа сжимается"
    additional_cost_annual_rub: 12000000
    revenue_impact_pct: -25
    probability_estimate: 0.25
    ebitda_after_rub: ...
  D_model_collapses:
    description: "Уход собственника ломает sales pipeline, потеря >40% recurring"
    additional_cost_annual_rub: 14000000
    revenue_impact_pct: -45
    probability_estimate: 0.10
    ebitda_after_rub: ...   # часто < 0
```

Probability — **expert judgment**, не precise. Сумма = 1.0.

`weighted_ebitda_after_rub` = Σ (probability × ebitda_after) — для torgavnoy позиции и IC-memo.

### Step 5: Открытые вопросы (то, что нельзя понять только по документам)

Этот блок — обязательный output. Документы не показывают:
- Готовность собственника остаться post-close (6 мес / 12 / 24)
- Реальную силу личных связей с топ-клиентами
- Кто из текущей команды может вырасти в замену
- Реалистичность найма Commercial Director в регионе

→ передаётся в P6.5 followup как `catalog_id: owner_dependency_interview` (вопросы для следующего звонка/встречи с продавцом).

### Step 6: Output

**Frontmatter:**
```yaml
owner_dependency:
  cash_extraction_annual_rub: 13500000
  functions_count: 5
  critical_functions: ["sales", "owner_relationships"]
  replacement_cost_annual_rub: 10200000
  replacement_cost_one_time_rub: 5000000     # retention bonus
  scenarios:
    A_stable: { probability: 0.20, ebitda_rub: ... }
    B: { probability: 0.45, ebitda_rub: ... }
    C: { probability: 0.25, ebitda_rub: ... }
    D: { probability: 0.10, ebitda_rub: ... }
  weighted_ebitda_after_rub: ...
  open_questions_for_seller: 7
  confidence: medium
```

## Output contract

См. [PIPELINE_SCHEMA.md](../../../../../PIPELINE_SCHEMA.md), объект `OwnerDependencyAssessment`. **Consumers:** P0 (weighted EBITDA — поправка к baseline), P4 (retention bonus structure, earn-out), P6.7 (concerns + valuation_range), P7 (Сценарий D probability >15% → Tier 2).

## Failure modes & guardrails

- **Probabilities — expert judgment.** Должны быть явно помечены так. Не выдавать за «расчёт».
- **Не считать функции, которых не было.** Если собственник не занимается продажами лично (есть sales-team) — не моделировать sales replacement.
- **Retention bonus к собственнику** — это часть price (структурируется через SPA), а не операционный расход. Учитывается в SPA totals, не дублируется в annual cost.
- **Open questions блок обязателен.** Если документов хватило на полную модель — это знак, что собственника недооценили (или документы не реалистичны).

## Связанные скиллы

- **Prerequisites:** P1.5 (cash extraction), P0 (baseline EBITDA), P1.8 (owner-relationship clients)
- **Downstream:** P0 (weighted EBITDA correction), P4, P6.7, P7
