---
name: ru-valuation-basis-extract
description: Extract from seller documents and conversations the basis on which the seller justifies the asking price — payback in N years, EBITDA multiple, revenue multiple, or hybrid. Compare against the actual detectable EBITDA (both pre-whitening and post-whitening from P0). Without this, the whitening_gap "hangs in the air" — unclear what base the seller is selling against. Triggers on "valuation basis", "на чём цена", "payback продавца", "мультипликатор", "price basis".
---

# Valuation Basis Extract (P1.7)

Продавец называет цену. Эта цена опирается на какую-то базу: «3× EBITDA», «окупаемость 4 года», «выручка × 1.2», «по аналогу — соседний аутсорс продали за X». **Без явного извлечения этой базы whitening_gap из P0 — это «расхождение чего с чем» в вакууме.** Нужно прибить gap к конкретной формуле продавца, чтобы потом торговаться по цифрам, а не «вы заломили».

## When to use

- Завершён P0 `ru-whitening-math` (есть detected EBITDA в нескольких сценариях)
- Есть финмодель продавца ИЛИ переписка / устные комментарии о цене
- Перед формированием preliminary_valuation_range в P6.7 outbound pack
- Перед IC-memo / решением идти ли в LOI

## Inputs

- Финмодель продавца (Excel) — если есть
- Любые письменные сообщения от продавца с упоминанием цены, окупаемости, мультипликатора
- Презентация продавца («тизер»), если есть
- Транскрипты звонков (Granola, если интегрировано)
- Whitening output (P0): `ebitda_reported`, `ebitda_white_baseline`, набор сценариев

## Workflow

### Step 1: Извлечь все упоминания цены и её обоснования

Сканировать все материалы продавца. Извлекаем явные/неявные:

| Тип базы | Что искать | Пример |
|---|---|---|
| Payback (срок окупаемости) | «окупаемость», «срок возврата», «N лет» | «бизнес окупится за 4 года» |
| EBITDA-мультипликатор | «N × EBITDA», «N × прибыль» | «3× прибыль 2024» |
| Revenue-мультипликатор | «N × выручка», «N × оборот» | «1.5× годовой оборот» |
| Сравнение с аналогом | «как X продали за Y» | «аналогичный кейс — 80 млн» |
| DCF-подобие (редко у МСБ) | «дисконтированные потоки» | — |
| Asset value | «стоимость техники / лицензий + …» | редко самостоятельно |
| Founder ask (без базы) | «хочу X миллионов» | классика МСБ |

Если несколько баз упоминается — извлечь все, отметить приоритет (что повторяется чаще / на чём настаивает).

### Step 2: Зафиксировать формулу

Для каждой найденной базы:

```yaml
- basis_type: ebitda_multiple
  multiplier: 3.0
  applied_to_metric: ebitda_2024_reported
  applied_to_value_rub: 22000000
  implied_price_rub: 66000000
  source: "письмо продавца 2026-03-12"
  confidence: high
```

Если product базы (`price = X × Y`) — рассчитать `implied_price`. Если payback — обратная формула: `implied_price = payback × annual_ebitda`.

### Step 3: Сопоставить с whitening-сценариями

Для каждой найденной базы:
1. Пересчитать формулу на whitened EBITDA из P0 (сценарии A/B/C).
2. Получить **«справедливую цену по той же формуле, но на белых цифрах»**.

```
implied_price_seller   = multiplier × ebitda_reported
implied_price_whitened = multiplier × ebitda_white_scenario_A
price_basis_gap_rub    = implied_price_seller − implied_price_whitened
price_basis_gap_pct    = price_basis_gap_rub / implied_price_seller × 100
```

**Это и есть основная торговая позиция:** «вы хотите 66 млн = 3× EBITDA. На посделочной EBITDA та же формула даёт 34 млн. Разница 32 млн — whitening gap, который ляжет на нас».

### Step 4: Контр-предложение (внутреннее, не для продавца)

Сформировать диапазон цены **в той же логике, что использует продавец** (чтобы дискуссия была в одной системе координат):

```yaml
counter_offer_range:
  low_rub: 28000000     # whitened EBITDA × multiplier − tax_risk_reserve
  base_rub: 34000000    # whitened EBITDA × multiplier
  high_rub: 38000000    # whitened EBITDA × multiplier + IT-льгота premium
  formula: "EBITDA_white_scenario_A × seller_multiplier"
  adjustments:
    - tax_risk_reserve_rub: 6000000     # из P1
    - it_accreditation_premium_rub: 4000000  # если льгота устойчива
  internal_note: "не раскрывать high до второй итерации"
```

Это уходит **в P6.7 internal_only_appendix**, не в outbound pack.

### Step 5: Output

**MD-секция `## Valuation basis`:**

```markdown
## Valuation basis

### Заявленная база продавца
- Формула: 3.0× EBITDA 2024
- Метрика: EBITDA = 22 000 000 ₽ (по управ.учёту)
- Implied price: 66 000 000 ₽
- Источник: письмо 2026-03-12, подтверждено созвоном 2026-03-15
- Confidence: high

### Та же формула на whitened-EBITDA (из P0)
| Сценарий | EBITDA, ₽ | Implied price (3×), ₽ | Gap к asking |
|---|---|---|---|
| Reported (как считает продавец) | 22M | 66M | — |
| A. White, ИТ-льгота, без retention | 11.4M | 34.2M | −31.8M (−48%) |
| B. White, без ИТ-льготы | 8.7M | 26.1M | −39.9M (−60%) |
| C. White + retention | 9.5M | 28.5M | −37.5M (−57%) |

### Главная торговая позиция
Asking price 66M предполагает базу EBITDA 22M. Реконструированная EBITDA на whitened-цифрах: 11.4M (baseline). Та же формула продавца даёт fair price ~34M.

Дополнительно: tax-risk reserve (P1) = 14.8M base estimate → escrow / price adjustment.

### Counter-offer range (internal, не для продавца на старте)
[см. internal_only_appendix в P6.7]
```

**Frontmatter:**

```yaml
valuation_basis:
  seller_basis:
    type: ebitda_multiple
    multiplier: 3.0
    applied_to_metric: ebitda_2024_reported
    applied_to_value_rub: 22000000
    implied_price_rub: 66000000
    confidence: high
    source: "письмо 2026-03-12"
  alternative_bases_mentioned:
    - type: payback
      years: 4.0
      confidence: medium
  whitened_recompute:
    scenario_A:
      ebitda_rub: 11400000
      implied_price_rub: 34200000
      gap_to_asking_rub: -31800000
      gap_to_asking_pct: -48.2
    scenario_B:
      ebitda_rub: 8700000
      implied_price_rub: 26100000
      gap_to_asking_rub: -39900000
  counter_offer_range_rub:
    low: 28000000
    base: 34000000
    high: 38000000
    internal_only: true
```

## Output contract

См. [PIPELINE_SCHEMA.md](../../../../../PIPELINE_SCHEMA.md), объект `ValuationBasis`. **Producer:** этот скилл. **Consumers:** P6.7 (preliminary_valuation_range + internal_only_appendix), P4 (SPA — формирование structure с учётом gap), P7 (gap >50% часто => Tier 2 для калибровки).

## Failure modes & guardrails

- **Если продавец цену не озвучивал** — output `seller_basis: not_stated` + явный запрос в P6.5 followup. **Не угадывать.**
- **Если продавец озвучил несколько баз** (типично: «4 года окупаемости ИЛИ 3× EBITDA, что больше») — извлечь все, в counter-offer использовать ту, которая выгоднее покупателю (меньшая implied_price). Отметить.
- **Если упоминание неформально** («ну около X») — `confidence: low`, явно отметить «требует подтверждения».
- **Не раскрывать high counter-offer на старте.** Это `internal_only: true` всегда.
- **Не объявлять контр-цену как «справедливую»** — это «та же формула продавца на белых цифрах». Финальное решение по цене — за человеком.

## Связанные скиллы

- **Hard prerequisite:** P0 `ru-whitening-math` (без whitened сценариев counter-recompute невозможен)
- **Soft prerequisite:** P1 `ru-tax-risk-scan` (для tax-risk reserve в counter-offer)
- **Downstream:** P6.7 (deliverable pack), P4 (SPA), P7 (escalation)
