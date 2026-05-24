---
name: ru-whitening-math
description: Reconstruct the target's economics as if it operated fully in the white (full OSNO tax regime, all employees on labor contracts, no hidden cash, consolidated related parties). Produces post-deal EBITDA, white payback, and whitening gap (delta between seller-claimed and reconstructed figures). The single most important skill in the RU pipeline — without it all valuation math is a mirage. Triggers on "whitening", "обеление", "post-deal EBITDA", "white payback", "пересчёт в белую", "whitening gap".
---

# Whitening Math (P0)

Большинство МСБ ИТ-аутсорсеров работают в серой/гибридной схеме: 10–12 «сотрудников» оформлены как ИП на УСН-6% или самозанятые, часть выручки идёт через связанные ИП на патенте, часть ЗП — в конвертах, лицензии и оборудование оформлены на собственника. **Покупатель работает в белую.** После сделки таргет переходит на ОСНО, все схемы обнуляются.

**EBITDA продавца ≠ EBITDA покупателя.** Этот скилл явно пересчитывает экономику в «белую» **до** обсуждения цены.

## When to use

- В пакете есть управленческий ОПиУ и/или финмодель продавца с заявленной EBITDA
- Известна структура занятости (ИП/самозанятые/ТД) — хотя бы оценочно
- Завершён P0.5 `ru-multi-entity-recon` (есть консолидированная база группы)
- Завершён (или параллелен) P1.5 `ru-cost-allocation-audit` (owner compensation отделена от прочих расходов)

**Hard prerequisite:** consolidated group P&L из P0.5. Без неё whitening считается по одному юрлицу и систематически занижает базу.

## Inputs

**Обязательно:**
- Consolidated group P&L (выход P0.5) — выручка, расходы, EBITDA до whitening
- Структура занятости: количество людей по статусу (ТД / ИП / самозанятый / неоформленные), их функции
- Owner compensation (из P1.5) — сколько и как собственник забирает
- Применимый налоговый режим: текущий (УСН/патент) и целевой (ОСНО)

**Желательно:**
- Реальные ставки ЗП по позициям (рыночные в регионе) — иначе используем reference table
- Статус ИТ-аккредитации Минцифры (есть/нет/планируется) + оценка устойчивости из P2
- Финмодель продавца (для `ru-finmodel-rewrite` под-блока)

## Workflow

### Step 1: Baseline — заявленная EBITDA

Зафиксировать **как продавец считает**:
- Заявленная выручка группы (consolidated, после Step 5 в P0.5)
- Заявленные расходы группы
- Заявленная EBITDA
- Заявленный мультипликатор / payback (вход в P1.7 `ru-valuation-basis-extract`)

Это **точка отсчёта** для расчёта whitening gap. Никаких корректировок на этом шаге.

### Step 2: Whitening adjustments — построение реконструированных расходов

Применяем по слоям. Каждая корректировка — отдельная строка с источником и допущением.

#### 2.1. Payroll reconstruction (главный блок)

Для каждой группы «сотрудников»:

| Текущий статус | После обеления | Что добавляется к расходам |
|---|---|---|
| ИП на УСН-6% (платит сам) | ТД | Δ к gross ЗП до рыночной + страховые 30% (или 7.6% если ИТ-аккр. устойчива) + НДФЛ 13/15% уже включён в gross |
| Самозанятый (НПД 6%) | ТД | То же + НДФЛ + страховые |
| Неоформленный (конверт) | ТД | Полная легализация: gross ЗП + НДФЛ + страховые |
| Уже ТД | ТД | Без изменений (но проверить, что gross соответствует рынку — иначе тоже корректировка) |

**Ключевые параметры** (вынесены в `params.yaml` скилла):
- `insurance_rate_default: 0.30`
- `insurance_rate_it_accredited: 0.076`
- `ndfl_rate: 0.13` (или 0.15 для дохода >5 млн ₽/год)
- `region_salary_table`: ссылка на reference (если есть) или явный input
- `gross_to_net_ratio`: 1.149 (для НДФЛ 13%)

**Output:** Δ payroll = новый ФОТ полностью обеленный − текущий ФОТ + ИП-выплаты + самозанятые-выплаты + конверт-оценка.

#### 2.2. Tax regime switch

Если целевой режим — ОСНО (так и есть для нашего покупателя):

| Налог | Текущий (УСН/патент) | После обеления (ОСНО) | Δ |
|---|---|---|---|
| Налог на прибыль | 0 (УСН доход-расход 15%) или 6% (УСН доход) | 25% (или 5% если ИТ-льгота устойчива) | Считать на whitened EBT |
| НДС | 0 | 22% с 2026 (если выручка >60 млн — на ОСНО обязательно) | + НДС с реализации − НДС к вычету по покупкам |
| Имущество | 0–2.2% (от кадастра) | 2.2% если есть недвижимость на ЮЛ | обычно ≈ 0 для аутсорса |

**Параметры:**
- `profit_tax_default: 0.25`
- `profit_tax_it_accredited: 0.05`
- `vat_rate_2026: 0.22`
- `vat_assumption_input_ratio`: доля закупок с НДС от выручки — критичная переменная. По умолчанию консервативно 0.10 (низкий вычет — у аутсорса основное это ФОТ, не закупки).

**Output:** Δ taxes = new tax burden (profit + НДС с учётом вычетов) − seller's reported taxes.

#### 2.3. Related-party consolidation cleanup

Из P0.5 уже есть intra-group flows. На этом шаге:
- Платежи на ИП собственника, маркированные в P0.5 как «вывод» (без явной экономической цели), **остаются в расходах группы** (это и есть owner compensation, не «реальный расход»). См. P1.5 для финальной нормализации.
- Внутригрупповые услуги между entities группы — элиминированы ещё в P0.5.
- Если в группе был ИП собственника, **не включаемый в сделку**, его выручка/расходы исключаются полностью, а функции, которые он выполнял, переоцениваются как «надо нанять/ переоформить» (вход в P2.7 owner-dependency-model).

#### 2.4. Hidden cash / конверты

Косвенная оценка по двум методам:
1. **ФОТ vs среднесписочная:** если заявленный ФОТ / СЧР < региональной средней ЗП × 12 × СЧР × 0.8 — разница потенциально в конверте.
2. **Прямой ответ продавца** на «обеляющий» вопрос (если есть).

Output: оценочная сумма конверта в год → +полная легализация в payroll (2.1).

### Step 3: Post-deal EBITDA

```
EBITDA_white = Revenue_consolidated
             − COGS_consolidated
             − Payroll_reconstructed       # из 2.1
             − Overheads_normalized        # из P1.5
             − Taxes_OSNO                  # из 2.2 (без profit tax — он считается на EBT)

EBITDA_white_with_IT_accreditation     = ...  # сценарий A (льгота сохранится)
EBITDA_white_no_IT_accreditation       = ...  # сценарий B (льгота слетит — из P2)
EBITDA_white_with_retention_payments   = ...  # сценарий C (минус retention key people из P4)
```

Минимум 3 сценария. Если есть гос-клиенты с риском change-of-control (из P1.8) — добавить сценарий D с потерей top-N клиентов.

### Step 4: White payback

Для каждого сценария:
```
Payback_white_years = Deal_price / EBITDA_white
```

Сравнить с заявленным продавцом payback (из Step 1 / P1.7).

### Step 5: Whitening gap

```
whitening_gap_abs_rub = EBITDA_reported − EBITDA_white_baseline
whitening_gap_pct     = whitening_gap_abs_rub / EBITDA_reported × 100
payback_gap_years     = Payback_white_baseline − Payback_reported
```

**`baseline` = средний сценарий** (обычно A с IT-аккр., без retention) — фиксируется явно.

### Step 6: Finmodel rewrite (под-блок)

Если у продавца есть финмодель Excel:
1. Извлечь допущения: рост цен / инфляция / рост ФОТ / ставки ЗП / horizon
2. Заменить допущения на whitened-параметры (страховые 30%/7.6%, ОСНО, реальные ЗП)
3. Пересчитать прогнозную EBITDA и payback на горизонте модели
4. Подсветить **whitening_gap_dynamic** — как gap меняется по годам
5. Сохранить переигранную модель рядом с оригиналом: `deals/<target>/whitened/finmodel_whitened.xlsx`

### Step 7: Output

**MD-секция `## Whitening adjustment`:**

```markdown
## Whitening adjustment

### Сводка
| Метрика | Заявлено продавцом | Реконструировано в белую | Δ |
|---|---|---|---|
| Выручка (consolidated) | … | … | … |
| EBITDA | … | … | … (gap = X%) |
| Payback, лет | … | … | … |

### Сценарии post-deal EBITDA
| Сценарий | Допущения | EBITDA, ₽ | Payback, лет |
|---|---|---|---|
| A. С ИТ-льготой, без retention | … | … | … |
| B. Без ИТ-льготы | … | … | … |
| C. С retention key people | … | … | … |
| D. С потерей top-N клиентов | … | … | … |

### Структура whitening adjustments (по слоям)
| Слой | Δ к расходам, ₽ | Источник / допущение |
|---|---|---|
| Payroll reconstruction (ИП→ТД) | +… | …человек по…ставке |
| Самозанятые → ТД | +… | … |
| Конверты → легализация | +… | оценка ФОТ vs СЧР |
| Налоги УСН → ОСНО (profit) | +… | … |
| НДС с 2026 (input vat = X%) | +… | … |
| ИТ-льгота (если применима) | −… | страховые 30% → 7.6% |

### Открытые вопросы для продавца
[в P6.5 с catalog_id]
```

**Frontmatter блок:**

```yaml
whitening:
  ebitda_reported_rub: 22000000
  ebitda_white_baseline_rub: 11400000
  whitening_gap_abs_rub: 10600000
  whitening_gap_pct: 48.2
  payback_reported_years: 3.2
  payback_white_baseline_years: 6.1
  payback_gap_years: 2.9
  scenarios:
    - id: A
      label: "С ИТ-льготой, без retention"
      ebitda_rub: 11400000
      payback_years: 6.1
      assumptions: ["it_accreditation_stable", "no_retention_bonuses"]
    - id: B
      ebitda_rub: 8700000
      payback_years: 8.0
      assumptions: ["it_accreditation_lost"]
  adjustments:
    - layer: payroll_ip_to_labor_contract
      delta_rub: 4800000
      people_count: 8
      source: "управ.учёт + ответ продавца DD-Q-014"
    - layer: tax_osno_profit
      delta_rub: 2200000
    - layer: vat_2026
      delta_rub: 1900000
      input_vat_ratio: 0.10
  confidence: medium
  blockers: []
```

## Output contract

См. [PIPELINE_SCHEMA.md](../../../../../PIPELINE_SCHEMA.md), объект `WhiteningAssessment` (поля выше — авторитативная форма). **Producer:** этот скилл. **Consumer-ы:** P1.7 (valuation basis — для сравнения с базой продавца), P6.7 (seller deliverable pack — для preliminary_valuation_range), P7 (escalation router — gap >40% часто триггерит Tier 2/3), P6 (md-report-builder — финальная сборка).

## Failure modes & guardrails

- **Никаких юридических заявлений.** «Признаки оптимизации» / «реконструкция при допущении X», не «продавец уклоняется от налогов».
- **Все ключевые параметры — явные.** Никаких hard-coded ставок ЗП внутри расчётов: всё через `params.yaml` + explicit input.
- **Если нет данных по структуре занятости:** не считать payroll reconstruction вслепую — `confidence: low`, явный запрос в seller-feedback (catalog_id для «structure_of_employment»).
- **ИТ-льгота — отдельная переменная, не дефолт.** Сценарий A применяется ТОЛЬКО если P2 `ru-it-accreditation-check` подтвердил устойчивость. Иначе baseline = сценарий B.
- **НДС input vat ratio — критичный input.** Если нет данных по структуре закупок — два сценария (0.05 / 0.15) и явная нотация.
- **Whitening gap >60%** или **payback gap >5 лет** → автоматический флаг для эскалации в Tier 2 (см. P7).
- **Один источник истины для consolidated baseline** — выход P0.5. Не пересчитывать здесь.

## Связанные скиллы

- **Hard prerequisite:** P0.5 `ru-multi-entity-recon`
- **Soft prerequisites:** P1.5 `ru-cost-allocation-audit`, P2 `ru-it-accreditation-check` (для сценария A vs B)
- **Параллельно:** P1 `ru-tax-risk-scan` (whitening — это «как должно быть»; tax-risk — «риск, что прошлое прилетит обратно»)
- **Downstream:** P1.7, P2.7, P4, P6.7, P7
- **Sub-skill:** `ru-finmodel-rewrite` (Step 6, может быть вынесен в отдельный скилл если разрастётся)
