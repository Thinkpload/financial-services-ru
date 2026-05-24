---
name: ru-client-base-quality
description: Per-client deep dive into the target's client base — services per client, recurring vs one-time, contract start date, calculated LTV, transferability risk, change-of-control exposure. Produces customers[] array for the company portrait. For IT-outsourcing, recurring contracts (1С:ИТС, 1С:ФРЕШ, обслуживание) are the main valuation driver and must be split from one-time hardware/project revenue. Triggers on "client base", "клиентская база", "LTV", "concentration", "change-of-control", "customer analysis".
---

# Client Base Quality (P1.8)

Для ИТ-аутсорса клиентская база — **основной актив**. Не «сколько клиентов», а: какие услуги под каждым, есть ли подписка, давно ли с нами, переживёт ли клиент смену собственника. Generic «top-10 concentration» не покрывает это. Recurring (1С:ИТС, ИТ-обслуживание) против one-time (оборудование, разовые внедрения) — драйвер мультипликатора оценки в 2-3 раза.

## When to use

- Завершён P0.5 (multi-entity — общие клиенты группы выявлены)
- Есть выгрузка по клиентам с выручкой (псевдонимизированно ок)
- Есть хотя бы образцы договоров топ-клиентов (на чтение или в шаблоне)
- Параллельно с P1.5 `ru-revenue-by-direction` (откуда берётся split по направлениям)

## Inputs

**Обязательно:**
- Список клиентов с выручкой за 3 года (псевдонимы клиентов ок)
- Разрез по услугам/направлениям на каждого клиента (1С:ИТС, обслуживание, оборудование, разовые)
- Дата начала отношений по каждому ключевому клиенту

**Желательно:**
- Договоры с топ-5-10 клиентами (на чтение, ищем change-of-control + срок)
- ARR/MRR по каждому recurring контракту
- Anonymizer mapping — чтобы сшивать одного клиента между документами (выручка ↔ договор ↔ ОСВ)

## Workflow

### Step 1: Сшивка клиентов между документами

Клиент `Клиент-12` в файле выручки = `LOC-007` в ОСВ = «крупный банк» в договоре? Без сшивки per-client разрез невозможен.

Использовать [tools/anonymize/](../../../../../tools/anonymize/) mapping (`mapping.json` сделки). Если псевдонимы не маппятся — задача оператору ручного маппинга (записать в `client_mapping_manual.json`).

### Step 2: Per-client разбор

Для каждого клиента (минимум — топ-20 по выручке, либо до 80% выручки):

```yaml
- client_pseudonym: CLIENT-007
  industry: "банк (по контексту)"
  relationship_start: 2019-04
  years_with_target: 6.5
  services:
    - type: 1c_its
      arr_rub: 480000
      recurring: true
    - type: it_obsluzhivanie
      arr_rub: 2400000
      recurring: true
    - type: hardware_purchases
      revenue_2024_rub: 1200000
      recurring: false
  revenue_total_2024_rub: 4080000
  revenue_share_in_target_pct: 4.7
  recurring_share_pct: 71.3
  contract:
    available: true
    duration_months: 12
    auto_prolongation: true
    change_of_control_clause: present
    change_of_control_terms: "право расторжения в течение 30 дней при смене бенефициара"
    notice_period_days: 60
  ltv_calculation:
    avg_annual_recurring_rub: 2880000
    estimated_remaining_years: 4.0
    discount_rate: 0.20
    ltv_rub: 7800000
  transferability:
    risk_level: medium
    reasons: ["change-of-control clause требует уведомления", "owner personal relationship"]
  notes: "крупнейший клиент, основной recurring driver"
```

**LTV formula** (упрощённая, фиксированная для сопоставимости между сделками):
```
LTV = avg_annual_recurring × estimated_remaining_years × (1 / (1 + discount_rate))^avg_year
```
- `estimated_remaining_years`: дефолт 4.0 для recurring без явных угроз; 2.0 если есть change-of-control риск; 1.0 если owner-dependent
- `discount_rate`: дефолт 0.20 (высокая ставка для МСБ ИТ-аутсорса)

Параметры явные, в `params.yaml`. Не подгонять под результат.

### Step 3: Сегментация клиентов

| Сегмент | Критерий | % выручки | Risk |
|---|---|---|---|
| Anchor recurring | recurring >70%, >3 года, без CoC-риска | … | low |
| Anchor mixed | recurring + one-time, важный по выручке | … | low/medium |
| Pure one-time | hardware/проекты, нет подписки | … | high (не воспроизводится) |
| At risk | CoC clause + owner-dep + большой share | … | high |
| Tail | <1% выручки каждый | … | n/a |

### Step 4: Концентрация (top-N)

| Метрика | Значение |
|---|---|
| Top-1 client share % | … |
| Top-3 client share % | … |
| Top-10 client share % | … |
| Top-1 recurring revenue share % | … |
| Effective concentration (HHI) | … |
| **Concentration after group consolidation** (если общие клиенты из P0.5) | … |

Концентрация на уровне группы (после consolidation) — отдельная важная цифра: часто резко выше, чем на каждом юрлице отдельно.

### Step 5: Change-of-control exposure

Сводно по топ-N клиентам:
```yaml
coc_exposure:
  contracts_reviewed: 8
  with_coc_clause: 5
  with_termination_right: 3
  with_consent_requirement: 2
  total_revenue_at_coc_risk_rub: 18500000
  total_revenue_at_coc_risk_pct: 21.4
```

Это **критическая цифра для P4 SPA** — определяет, что нужно делать pre-close (получать согласия / notify) и какой % выручки под риском post-close.

### Step 6: Recurring vs one-time split

Из per-client данных:
```yaml
revenue_split_2024:
  recurring_rub: 58000000
  recurring_pct: 67.0
  one_time_rub: 28000000
  one_time_pct: 32.4
  hardware_pass_through_rub: 12000000   # отдельно — низкая маржа
```

Передаётся в P1.5 `ru-revenue-by-direction` для cross-check, в P0 для оценки качества post-deal EBITDA (recurring оценивается выше).

### Step 7: Output

**MD-секция `## Client base quality`:**

```markdown
## Client base quality

### Сводка
| Метрика | Значение |
|---|---|
| Клиентов всего активных | … |
| Top-3 концентрация | …% |
| Recurring share | …% |
| Total LTV (top-20) | … ₽ |
| Revenue at CoC risk | …% / … ₽ |
| Средний срок отношений (weighted) | … лет |

### Per-client breakdown (top-20)
[таблица из Step 2]

### Сегментация
[таблица из Step 3]

### Change-of-control exposure
[блок из Step 5]

### Передаётся в:
- P4 SPA: % выручки под CoC риском → стратегия pre-close consents
- P0 whitening сценарии: recurring share → confidence в EBITDA forward
- P6.7 outbound pack: strengths (recurring share, средний срок) и concerns (concentration, CoC)
```

**Frontmatter:** структура `client_base_assessment` со всеми полями выше + массив `customers[]`.

## Output contract

См. [PIPELINE_SCHEMA.md](../../../../../PIPELINE_SCHEMA.md), объект `ClientBaseAssessment` с подмассивом `customers[]`. **Producer:** этот скилл. **Consumers:** P4 (CoC strategy), P0 (recurring quality для EBITDA forward), P6.7 (strengths/concerns), P7 (CoC risk >25% выручки → Tier 2).

## Failure modes & guardrails

- **Не считать LTV если нет recurring структуры.** Если все one-time — `ltv_rub: not_applicable`, не подгонять.
- **Не публиковать имена клиентов в outbound pack.** Использовать псевдонимы. Real names только в internal версии.
- **Если договоры топ-клиентов недоступны** — CoC analysis по типовому шаблону + явный запрос продавцу. `confidence` соответствующий.
- **HHI расчёт** требует ≥10 клиентов. На малой базе использовать только top-N share %.
- **LTV — это не fair price клиента**, это «текущая стоимость ожидаемых будущих recurring потоков при допущениях X». Никогда не использовать LTV в outbound pack без явных параметров.

## Связанные скиллы

- **Prerequisites:** P0.5 (общие клиенты группы), anonymizer mapping
- **Параллельно:** P1.5 `ru-revenue-by-direction`
- **Downstream:** P4 (CoC strategy), P0 (recurring confidence), P6.7, P7
