---
name: ru-it-accreditation-check
description: Verify the target's Минцифры IT-accreditation status (or assess feasibility if planned), and quantify the sustainability of associated tax benefits after the deal. Benefits — страховые 7.6% vs 30%, налог на прибыль 5% vs 25% — significantly change post-deal EBITDA. Produces a "льгота устойчива/неустойчива" verdict that gates whitening scenario A vs B in P0. Triggers on "ИТ-аккредитация", "Минцифры реестр", "ИТ-льгота", "7.6%", "5% налог", "IT-tax-benefit".
---

# IT Accreditation Check (P2)

ИТ-льгота (страховые 7.6%, налог на прибыль 5% по профильной выручке) — большой переменный фактор в post-deal EBITDA. Может дать +30-40% к whitened EBITDA. Но льгота **условна и проверяется ежегодно** — если после сделки доля ИТ-выручки упадёт ниже 70% или СЧР ниже 7 — льгота слетает, причём с пересчётом задним числом.

Этот скилл даёт **verdict устойчивости** льготы → выбирает baseline сценарий в P0.

## When to use

- В пакете есть упоминание ИТ-аккредитации (свидетельство, упоминание 7.6%/5%, профильный ОКВЭД 62.x)
- Перед запуском P0 — нужно знать, какой сценарий брать за baseline
- Перед SPA — для retention требований к ИТ-аккр. условиям

## Inputs

- ИНН таргета (для проверки в реестре Минцифры — публичный)
- Свидетельство об ИТ-аккредитации (если есть, дата выдачи)
- Структура выручки по ОКВЭД (профильная vs непрофильная) — из P1.5
- СЧР за последние периоды (из P0 / Rusprofile)
- Средняя ЗП по ТД-сотрудникам (из P0 payroll structure)
- Региональная средняя ЗП (reference table)
- Состав учредителей (нерезидентов нет → ок)

## Workflow

### Step 1: Текущий статус

- Есть ли в реестре Минцифры на сегодня (`https://www.gosuslugi.ru/ait/registry` — public)
- Дата получения, основание ОКВЭД
- Если нет — есть ли документы на подачу / план получения

### Step 2: Чек устойчивости (требования 2026)

Текущие требования (`params.yaml` — поддерживать актуальность):

| Требование | Целевое значение | Факт у таргета | Pass/Fail |
|---|---|---|---|
| Доля профильной ИТ-выручки | ≥ 70% | … | … |
| СЧР сотрудников (по ТД, **не ИП!**) | ≥ 7 | … | … |
| Средняя ЗП | ≥ региональной средней | … | … |
| Нерезиденты в учредителях с долей >50% | отсутствуют | … | … |
| Аккредитация не отозвана | да | … | … |

Критично: **СЧР считается по ТД**, не по ИП/самозанятым. Это часто и есть бутылочное горлышко для МСБ ИТ-аутсорса — на бумаге 5 сотрудников по ТД, остальные ИП. После whitening (P0) СЧР по ТД вырастет, но это **forward**, текущая аккредитация считается по **historical**.

### Step 3: Sustainability verdict

```yaml
verdict: stable | at_risk | unsustainable | not_applicable
reasons: [...]
break_even_metrics:
  it_revenue_share_pct_needed: 70
  it_revenue_share_pct_actual: 68      # на грани
  scnr_needed: 7
  scnr_actual: 5                        # недотягиваем
```

- `stable` — все требования выполнены с запасом >10%
- `at_risk` — одно требование на грани (±5%) или временно невыполнено
- `unsustainable` — требование явно не выполняется и не выправится после сделки
- `not_applicable` — аккредитации нет и план получения нереалистичен

### Step 4: Денежная оценка льготы

```
benefit_insurance_rub  = white_payroll × (0.30 − 0.076)
benefit_profit_tax_rub = ebitda_white × (0.25 − 0.05)
benefit_total_annual   = benefit_insurance + benefit_profit_tax
```

При `verdict = stable` → P0 baseline = сценарий A (с льготой)
При `at_risk` → P0 baseline = сценарий A но `confidence: medium`; сценарий B (без льготы) — основной для торга
При `unsustainable` → P0 baseline = сценарий B (без льготы)

### Step 5: Output

**Frontmatter:**
```yaml
it_accreditation:
  current_status: accredited | not_accredited | planned
  registry_check_date: 2026-05-24
  sustainability_verdict: at_risk
  benefit_annual_rub: 4200000
  benefit_5yr_rub: 21000000
  break_even_gaps:
    - metric: scnr
      gap: -2
      cure_path: "оформить ИП-сотрудников по ТД (см. P0 payroll reconstruction)"
  confidence: high
```

## Output contract

См. [PIPELINE_SCHEMA.md](../../../../../PIPELINE_SCHEMA.md), объект `ITAccreditationAssessment`. **Consumers:** P0 (scenario A vs B selection), P1 (forward IT-benefit downside risk), P4 (SPA retention conditions для аккредитации), P6.7 (strength для outbound pack если stable, concern если at_risk).

## Failure modes & guardrails

- **Реестр Минцифры — основной источник правды.** Свидетельство от продавца — только подтверждение, не замена.
- **СЧР считать БЕЗ ИП/самозанятых.** Это типичная ошибка анализа.
- **Если льгота получена недавно (<12 мес)** — `at_risk` по умолчанию (первая ежегодная проверка ещё не пройдена).
- **Cure path** должен быть реалистичным — не предлагать «нанять 5 человек» без оценки whitening-эффекта.

## Связанные скиллы

- **Prerequisites:** P0.5 + первичная оценка СЧР/ФОТ
- **Параллельно:** P1 (tax-risk использует verdict для downside scenario)
- **Downstream:** P0, P4, P6.7
