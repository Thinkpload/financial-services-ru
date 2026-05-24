---
name: ru-tax-risk-scan
description: Scan for Russian tax risks specific to small IT-outsourcing targets — дробление, 54.1 НК (IP-схема), УСН-limit proximity, IT-accreditation sustainability, hidden cash, НДС 22% from 2026. Produces a flag list with weight and monetary impact estimate (доначисления + пени + штрафы for 3 years ВНП — налоговые риски прошлого периода остаются на покупателе). Triggers on "tax risk", "налоговые риски", "дробление", "54.1", "УСН", "ИТ-льгота", "конверты", "НДС 22".
---

# Tax Risk Scan (P1)

Налоговые риски **прошлого периода** (3 года выездной налоговой проверки, ВНП) **остаются на покупателе** после сделки. SPA должен включать indemnity и/или escrow под эти риски (см. P4). Этот скилл квантифицирует риск в рублях для торга по цене и формирования escrow-suммы.

**Отличие от P0 whitening:** whitening — «как должно быть», tax-risk-scan — «риск, что прошлое прилетит обратно». Это **разные числа в SPA**: whitening корректирует цену, tax-risk корректирует структуру (indemnity/escrow).

## When to use

- Завершён P0.5 (есть карта группы юрлиц)
- Завершён или параллелен P0 (есть оценка реальной payroll-структуры и связанных сторон)
- Доступны: Rusprofile pull, ЕГРЮЛ-выписки, управ.учёт по контрагентам, штатная структура

## Inputs

- Список entities группы (P0.5) + флаги дробления (P0.5 Step 2)
- Структура занятости (ТД / ИП / самозанятые / неоформленные) — из P0 Step 2.1
- Выручка по годам по entities (за 3 года минимум) — для УСН-limit checking
- Список ключевых клиентов ИП-«сотрудников» (если ИП с одним клиентом — 54.1 флаг)
- Статус ИТ-аккредитации Минцифры (вход из P2)
- Региональная средняя ЗП для специальности (reference table или явный input)
- Rusprofile: налоговая дисциплина, задолженности, исп.производства

## Workflow

### Step 1: Дробление (splits)

Берём флаги из P0.5 Step 2. Здесь — **денежная оценка** риска переквалификации:

1. Если ФНС признает дробление → консолидирует выручку группы → пересчитывает налоги по ОСНО с момента превышения УСН-лимита.
2. **Оценка доначислений:**
   ```
   donachisleniya = (consolidated_revenue − usn_limit_per_year) × osno_tax_burden_rate
                    за каждый год последних 3
   peni            = donachisleniya × refinancing_rate × days_overdue / 365
   shtraf          = donachisleniya × 0.40   # ст. 122 НК п.3 — умысел
   ```
3. **Параметры** (в `params.yaml`):
   - `usn_revenue_limit_2024: 265800000` (с учётом коэффициента-дефлятора)
   - `usn_revenue_limit_2025: 450000000` (с 2025 повышен)
   - `osno_full_burden_estimate_rate: 0.20` (грубо, для сценарного расчёта; точный — через P0 whitening)
   - `vnp_horizon_years: 3`
   - `peni_rate_assumption: refinancing_rate × 1.5` (с 2024)
   - `shtraf_rate_intent: 0.40`, `shtraf_rate_no_intent: 0.20`

**Output:** оценка `dorbnyenie_risk_rub_low/base/high` (low — без умысла, high — с умыслом + полная консолидация).

### Step 2: 54.1 НК — ИП-схема (необоснованная налоговая выгода)

Признаки переквалификации ИП → ТД:
- ИП с **одним клиентом >70%** выручки за период
- ИП работает **на территории заказчика** (офис аутсорсера)
- Регулярность выплат, как зарплата (фиксированная сумма ежемесячно)
- Отсутствие других клиентов у ИП
- ИП открыт сразу после увольнения из таргета
- Виды деятельности ИП совпадают с трудовыми функциями
- Расходные документы ИП обеспечивает заказчик

**Оценка для каждого ИП-«сотрудника»:**
```
risk_per_ip = ip_annual_payment × (ndfl_rate + insurance_rate_default − usn_rate_paid_by_ip)
              × vnp_horizon_years
peni        = ...
shtraf      = risk_per_ip × shtraf_rate
```

`shtraf_rate` выбирается по количеству признаков 54.1: ≥4 → intent (0.40), 2-3 → no_intent (0.20), <2 → flag low.

**Output:** таблица — ИП → сумма за 3 года → веро­ятность переквалификации → impact_rub.

### Step 3: УСН-лимиты — близость к утрате режима

Для каждой entity на УСН:
```
proximity_pct_2024 = revenue_2024 / usn_revenue_limit_2024 × 100
proximity_pct_2025 = revenue_2025 / usn_revenue_limit_2025 × 100
```

Флаги:
- `proximity_pct > 85%` → **high** (один хороший месяц — слетит)
- `proximity_pct > 70%` → **medium**
- `> 100%` → **уже слетел** — критический риск, проверить, что РСБУ соответствует ОСНО (часто нет — это уже доначисления)

Денежная оценка перехода на ОСНО для каждой entity: ровно по логике Step 2 P0 (`ru-whitening-math`) с другим горизонтом — forward-looking.

### Step 4: ИТ-льгота — устойчивость

Вход из P2 `ru-it-accreditation-check`. Здесь:
- Если P2 говорит «льгота неустойчива» → downside-сценарий: страховые 7.6% → 30%, налог 5% → 25%.
- Денежная оценка: `delta_taxes = (rate_full − rate_it) × base × horizon`.
- Этот же сценарий уже считается в P0 как сценарий B — здесь дублируется для tax-risk summary, помечается `cross_ref: whitening.scenarios.B`.

### Step 5: НДС 22% с 2026

- Если выручка >60 млн ₽ → ОСНО обязательно с 2026 → НДС 22%.
- Если у таргета сейчас УСН + крупные клиенты на ОСНО, которые **хотят вычета НДС** — они уйдут или потребуют скидку 22% / (1+22%).
- Risk = `revenue_at_risk × 0.18` (грубая оценка потери маржи; точнее — через customer-by-customer в P1.8).

### Step 6: Конверты (hidden cash)

Косвенная оценка (та же, что в P0 Step 2.4): ФОТ vs СЧР × региональная ЗП.
- Если расхождение > 30% → флаг.
- Денежная оценка: `hidden_payroll × (ndfl + insurance) × vnp_horizon`.

Это **не повторяет** Step 2 P0 — там корректируется forward EBITDA; здесь — **historical risk** доначислений за 3 года ВНП.

### Step 7: Прочие красные флаги (из Rusprofile)

- **Налоговые задолженности** (публичные) → прямой риск ареста счетов
- **Исполнительные производства** → возможные скрытые обязательства
- **Арбитражные дела с ФНС** → активные споры
- **Реструктурированные задолженности** → косвенно по разнице «начислено vs уплачено»

Все — в таблицу флагов как есть, без денежной оценки (или с явным `impact_rub: unknown`).

### Step 8: Output

**MD-секция `## Tax risk scan`:**

```markdown
## Tax risk scan

### Сводная денежная оценка (за 3 года ВНП)
| Категория | Low estimate | Base | High estimate |
|---|---|---|---|
| Дробление (консолидация группы) | … | … | … |
| 54.1 НК (ИП-схема, N ИП) | … | … | … |
| УСН-limit утрата (entity X) | … | … | … |
| ИТ-льгота downside (forward) | … | … | … |
| НДС 22% с 2026 (forward) | … | … | … |
| Конверты (historical) | … | … | … |
| **Итого** | **…** | **…** | **…** |

### Флаги по категориям
- [high] (impact_rub: 8.5M base) Дробление: TARGET-A и TARGET-B имеют 45% общих клиентов → см. multi-entity recon
- [high] (impact_rub: 4.2M base) 54.1: 6 ИП с одним клиентом >70%, в офисе таргета
- [medium] (impact_rub: 2.1M base) УСН proximity TARGET-A 89% за 2024
- ...

### Рекомендация для SPA (передаётся в P4)
- Indemnity cap: base estimate × 1.5 (для умысла high estimate × 1.2)
- Escrow horizon: 3 года (горизонт ВНП)
- Escrow %: <предложение>
```

**Frontmatter:**

```yaml
tax_risk_scan:
  total_impact_low_rub: 8000000
  total_impact_base_rub: 14800000
  total_impact_high_rub: 24000000
  vnp_horizon_years: 3
  flags:
    - category: split
      severity: high
      impact_base_rub: 8500000
      cross_ref: "multi_entity_recon.split_signals"
    - category: 541_ip_scheme
      severity: high
      impact_base_rub: 4200000
      ip_count: 6
    - category: usn_limit
      severity: medium
      impact_base_rub: 2100000
      entity: TARGET-A
      proximity_pct: 89
    - category: it_accreditation_downside
      severity: medium
      impact_base_rub: 1800000
      cross_ref: "whitening.scenarios.B"
    - category: vat_2026
      severity: medium
      impact_base_rub: 1200000
    - category: hidden_cash
      severity: high
      impact_base_rub: 3500000
  recommendation_for_spa:
    indemnity_cap_rub_base: 22000000
    indemnity_cap_rub_high: 28800000
    escrow_horizon_years: 3
  confidence: medium
```

## Output contract

См. [PIPELINE_SCHEMA.md](../../../../../PIPELINE_SCHEMA.md), объект `TaxRiskAssessment`. **Producer:** этот скилл. **Consumer-ы:** P4 `ru-spa-risks` (indemnity/escrow sizing), P6.7 (preliminary valuation должна учитывать tax risk reserve), P7 (high estimate >30M ₽ — авто-эскалация в Tier 3).

## Failure modes & guardrails

- **Это сценарные оценки риска, не юридические заключения.** Все цифры — «при допущении X с вероятностью Y». Tier 3 (налоговый юрист) валидирует перед SPA.
- **Не дублировать с whitening.** Forward-looking ИТ-льгота downside помечается `cross_ref` к P0, не пересчитывается отдельно.
- **Если нет данных по ИП-сотрудникам** (имён клиентов, времени работы) — 54.1 оценка `confidence: low`, явный запрос продавцу.
- **VNP horizon = 3 года** — это default. Если есть признаки умысла (явное дробление + конверты + 54.1 вместе) — горизонт может быть продлён судом, добавить high-сценарий с horizon=10 (банкротство).
- **Никогда не маркировать «продавец уклоняется».** Только «признаки X, оцениваемый риск Y».

## Связанные скиллы

- **Prerequisites:** P0.5, P0, P2 (для ИТ-льготы downside)
- **Параллельно:** P3 `ru-152fz-check` (там — административные штрафы РКН, не налоговые; считать отдельно)
- **Downstream:** P4 (SPA indemnity/escrow), P6.7 (valuation), P7 (escalation)
