---
name: ru-spa-risks
description: Analyze risks and structure recommendations for a Share Purchase Agreement under Russian law for an IT-outsourcing MSB acquisition. Covers заверения об обстоятельствах (ст. 431.2 ГК), возмещение потерь (ст. 406.1 ГК), эскроу variants, ФАС approval thresholds, change-of-control in client contracts, non-compete under ст. 1033 ГК, retention bonuses, and indemnity sizing based on tax-risk and compliance outputs. Replaces upstream US-centric SPA assumptions. Triggers on "SPA", "share purchase", "indemnity", "escrow", "заверения", "non-compete", "ФАС", "retention bonus", "change-of-control".
---

# SPA Risks (P4)

Апстрим оперирует US-понятиями (representations & warranties, indemnification, MAC clause). РФ-право — другие институты с другой логикой. Этот скилл строит рекомендации по структуре SPA на основе выходов P1 (tax-risk), P1.8 (CoC), P2.8 (assets), P2.7 (owner-dependency), P3 (152-ФЗ/КИИ).

## When to use

- Завершены P1, P1.8, P2, P2.7, P2.8, P3 (нужны цифры risks для sizing)
- Перед LOI (для term sheet) ИЛИ перед SPA draft

## Inputs

- `tax_risk_scan` (P1) — для indemnity sizing
- `client_base_assessment.coc_exposure` (P1.8) — для pre-close consents strategy
- `asset_inventory` (P2.8) — для side-purchase clauses
- `owner_dependency` (P2.7) — для retention bonus / earn-out
- `it_accreditation` (P2) — для retention conditions на сохранение льготы
- `compliance_152fz_kii` (P3) — для отдельной indemnity по штрафам РКН
- Размер сделки и структура (cash vs deferred) — input

## Workflow

### Step 1: Заверения об обстоятельствах (ст. 431.2 ГК) — что обязательно

Чек-лист must-have заверений от продавца:

| Область | Заверение | Severity если ложное |
|---|---|---|
| Налоги | «нет неуплаченных налогов / не ведётся проверок / нет признаков 54.1 / нет дробления» | tax-risk impact |
| ИП-сотрудники | «нет трудовых отношений с ИП-контрагентами» | tax-risk impact |
| ПДн / РКН | «соблюдены требования 152-ФЗ, нет открытых предписаний» | штрафы РКН |
| КИИ / гос-клиенты | «выполнены требования 187-ФЗ при работе с КИИ» | расторжение контрактов + ст. 274.1 УК риск |
| Активы | «активы на балансе ЮЛ принадлежат ему, нет обременений» | переоформление + downtime |
| ИТ-аккредитация | «соответствует требованиям Минцифры, не получала уведомлений о пересмотре» | downside льготы |
| Клиенты | «нет уведомлений о расторжении / претензий top-10» | revenue at risk |
| Дочки / связанные | «полный список аффилированных лиц приложен» | дробление skeleton in closet |

Каждое ложное заверение → возмещение потерь по ст. 406.1 ГК (см. Step 2).

### Step 2: Возмещение потерь (ст. 406.1 ГК) и indemnity

В РФ — это **не indemnity в US-смысле**, это договорная обязанность возместить определённые имущественные потери при наступлении обстоятельства. Формулируется максимально конкретно: «если выявлены доначисления ФНС по основаниям X за периоды Y — продавец возмещает в размере Z».

**Sizing (берётся из P1 + P3):**

```yaml
indemnity_structure:
  total_cap_rub: 28800000               # P1 high estimate × 1.2 (+ P3 fines)
  uncapped_categories:
    - "умышленное искажение заверений"
    - "сокрытие фактов после проверки покупателя"
  capped_categories:
    - category: "tax_doначisleniya за 3 года ВНП"
      cap_rub: 22000000                 # P1 base × 1.5
      basket_rub: 500000                # «корзина» — собираем до этого порога, потом начинает работать
    - category: "штрафы РКН / нарушения 152-ФЗ"
      cap_rub: 2200000
      basket_rub: 100000
    - category: "переоформление активов сверх раскрытого"
      cap_rub: 1500000
    - category: "расторжение топ-клиентами по нераскрытым CoC основаниям"
      cap_rub: 5000000
  duration_years: 3                      # горизонт ВНП
  duration_years_tax: 3
  duration_years_other: 1
```

### Step 3: Эскроу

Варианты (`params.yaml`):

| Тип | Стоимость | Преимущества | Минусы |
|---|---|---|---|
| Нотариальный (с эскроу-агентом) | 1-3% от суммы | Самый «жёсткий» | Дорого |
| Банковский эскроу | 0.5-1% | Стандарт | Жёсткие условия раскрытия |
| Специальный счёт у одного из сторон | 0 | Дёшево | Слабая защита |

**Рекомендация по умолчанию для МСБ ИТ-аутсорса:**
```yaml
escrow_recommendation:
  type: bank_escrow
  amount_rub: 15000000                  # tax_risk_base
  pct_of_deal: 25                       # для сделки на 60M
  horizon_years: 3
  release_schedule:
    - after_year_1: 30%
    - after_year_2: 30%
    - after_year_3: 40%
  triggers_for_partial_release:
    - "закрытие ВНП за период"
    - "отсутствие претензий ФНС / РКН"
```

### Step 4: ФАС-согласование

```
needs_fas_approval = (combined_assets > threshold) OR (combined_revenue > threshold)
```

Пороги 2026 (`params.yaml`):
- Активы группы покупателя + таргета >800 млн ₽ → согласование
- Выручка предыдущего года >2 млрд ₽ → согласование

Для МСБ ≤100 млн обычно **не требуется**, но проверять.

### Step 5: Change-of-control strategy (из P1.8)

```yaml
coc_strategy:
  total_revenue_at_risk_pct: 21.4      # из P1.8
  pre_close_consents_needed: 5
  estimated_cure_cost_rub: 0           # обычно бесплатно если работаем заранее
  cure_timeline_weeks: 4-8
  fallback_if_refused:
    - "price adjustment / earn-out tied to retention"
    - "client retention guarantees от продавца"
```

### Step 6: Non-compete (ст. 1033 ГК)

В РФ non-compete для собственника **только на договорной основе и с ограничениями**:
- Не более 2-3 лет
- Конкретная территория и виды деятельности
- Должен быть **компенсирован** (иначе суд признает ничтожным)

```yaml
non_compete:
  duration_years: 2
  territory: "регион регистрации таргета + соседние субъекты"
  scope: "ИТ-аутсорс сисадминов, B2B"
  compensation_structure: "включена в SPA price (1.5% от deal price/year)"
```

### Step 7: Retention key persons

Из P2.7 — критические люди + сам собственник:

```yaml
retention_structure:
  - person: seller_owner
    type: retention_bonus_in_spa
    amount_rub: 5000000
    horizon_months: 12
    trigger: "оставаться full-time в роли консультанта"
    conditions:
      - "минимум 80% времени"
      - "сохранение топ-3 клиентов в первые 6 мес"
  - person: tech_lead_kp_001
    type: stay_bonus
    amount_rub: 1800000
    horizon_months: 18
    in_employment_contract: true
  - person: account_manager_kp_002
    type: stay_bonus
    amount_rub: 1200000
    horizon_months: 12
```

### Step 8: Output

**MD-секция `## SPA risks & structure recommendations`** + **frontmatter `spa_recommendations`** с indemnity / escrow / non-compete / retention блоками выше.

## Output contract

См. [PIPELINE_SCHEMA.md](../../../../../PIPELINE_SCHEMA.md), объект `SPARecommendations`. **Consumers:** P6 (financial report → SPA section), P6.7 (preliminary structure для outbound), P7 (если total indemnity_cap > deal_price × 0.5 → Tier 3 юриста обязателен).

## Failure modes & guardrails

- **Это рекомендации, не юр.документ.** Финальный SPA пишет российский юрист.
- **Заверения должны быть конкретными.** «Соответствует всем требованиям законодательства» — бесполезно в суде. Только перечислимые конкретные факты.
- **Non-compete без компенсации — ничтожен** в РФ. Явная компенсация обязательна.
- **Эскроу не покрывает умышленное сокрытие** — отдельная uncapped категория.
- **Retention bonus собственнику** = часть price (расход покупателя), не операционный расход (не путать в P0).
- **Если deal через cash + earn-out** — учесть, что earn-out часто оптимизируется продавцом в ущерб long-term ценности. Условия earn-out должны привязываться к чистым recurring метрикам, не EBITDA (которая управляема).

## Связанные скиллы

- **Prerequisites:** P1, P1.8, P2, P2.7, P2.8, P3
- **Downstream:** P6 (financial report), P6.7 (outbound — но только high-level), P7
