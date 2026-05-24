---
name: ru-dd-checklist
description: Russian-localized due diligence checklist for small IT-outsourcing M&A targets. Replaces the upstream generic dd-checklist with RU-specific workstreams: RSBU (not GAAP), УСН/ОСНО/dробление tax structure, 152-ФЗ/КИИ (not GDPR), multi-entity group structure, recurring revenue split by direction, owner dependency, and seller followup catalog integration. Triggers on "dd checklist", "due diligence", "что запросить у продавца", "data room", "DD-вопросы РФ".
---

# RU DD Checklist (адаптация апстрима под РФ ИТ-аутсорс)

Полностью заменяет апстримный `private-equity/dd-checklist` для целей данного плагина. Пробелы апстрима задокументированы в [BASELINE_FINDINGS.md](../../../../../BASELINE_FINDINGS.md) — этот скилл их закрывает.

**Принципиальное отличие:** упор не на «что в досье на закрытие», а на **«какие документы нужны для запуска пайплайна (P0–P7) с нужным confidence»**. Каждый запрос имеет привязку `needed_for: <skill>` — если документ не дают, понятно, какой блок анализа провалится.

## When to use

- На старте новой сделки (после первичного скрининга)
- При сборке `deals/<target>/checklist.md`
- Когда продавец прислал часть документов и нужно понять, чего ещё не хватает (передаётся в P6.5 `ru-seller-feedback-draft`)

## Workflow

### Step 1: Scope

Минимальный набор вопросов перед генерацией:
- Сделка: платформа / add-on / выкуп у собственника?
- Размер таргета: выручка / EBITDA / штат (хотя бы порядок)
- Структура: одно юрлицо / группа? ИП собственника есть?
- Гос-клиенты есть? (триггерит КИИ, ФСТЭК ветки)
- ИТ-аккредитация Минцифры есть/планируется?
- Желаемый timeline до LOI

### Step 2: Сгенерировать чек-лист по workstream-ам (РФ-специфика)

Стандартная таблица:

| ID | Workstream | Документ / артефакт | Приоритет | Status | `needed_for` (скилл) | Catalog ID (для P6.5) |
|---|---|---|---|---|---|---|

**Workstream 1: Group structure & corporate**

| Документ | Why |
|---|---|
| ЕГРЮЛ-выписки по всем юрлицам группы за 1 год | P0.5 multi-entity inventory |
| Список действующих ИП собственника и связанных лиц | P0.5 split detection |
| Структура акционеров с долями + историей изменений | P0.5 + P4 SPA |
| Управ.схема группы (кто кому подчинён, где какие функции) | P0.5 + P2.7 owner dependency |
| Rusprofile-отчёты по топ-3 entities + ИНН учредителей | P0.5 enrichment |

**Workstream 2: Финансы (РСБУ + управ)**

| Документ | Why |
|---|---|
| Бухотчётность РСБУ формы 1/2 (и 4 если есть) за 3 года по всем юрлицам | P5 audit |
| Управ.ОПиУ помесячно за 2 года + текущий год | P0 baseline, P3.5 monthly anomaly |
| ОСВ из 1С по контрагентам за последний год по каждому юрлицу | P0.5 intra-group flows + P1 51.1 detection |
| Методология распределения общих расходов | P1.5 cost allocation audit |
| Финмодель продавца с допущениями и чувствительностью | P0 finmodel rewrite |
| Отчёт по выручке по направлениям + recurring/one-time | P1.5 revenue-by-direction |
| Дебиторка/кредиторка с aging по контрагентам | усиленный P5 (АВЕ+Фомичев practice) |
| Налоговые декларации (УСН/ОСНО) за 3 года | P1 cross-check + P5 |
| Акты сверок с ФНС | P1 hidden tax debt detection |

**Workstream 3: Налоги / структура (РФ-специфика)**

| Документ | Why |
|---|---|
| Применяемый налоговый режим по каждой entity + история смен | P1 tax-risk-scan |
| Перечень ИП-«сотрудников» с функциями и сроками работы | P1 54.1 НК scan |
| Список самозанятых-подрядчиков с функциями | P1 + P0 payroll reconstruction |
| Свидетельство ИТ-аккредитации Минцифры (если есть) | P2 |
| Расчёт устойчивости ИТ-льготы (доля ИТ-выручки, СЧР, средняя ЗП) | P2 |
| Письма/уведомления ФНС за 3 года | P1 hidden risk detection |

**Workstream 4: Коммерческая часть**

| Документ | Why |
|---|---|
| Список клиентов с выручкой за 3 года (псевдонимизированно ок) | P1.8 client-base-quality |
| Список договоров с топ-10 клиентами (можно на чтение) | P1.8 + P4 change-of-control scan |
| Recurring revenue split: ARR/MRR по каждому recurring контракту | P1.5 + P1.8 |
| Срок действия, условия пролонгации, change-of-control оговорки | P4 SPA risks |
| Список ключевых поставщиков (1С, MS, лицензии) и условия | P2.8 asset-inventory |

**Workstream 5: Люди**

| Документ | Why |
|---|---|
| Штатное расписание (только штат по ТД) | P0 + P1 (vs ИП/самозанятые) |
| Среднесписочная численность за 3 года (СЧР) | P0 cross-check + P2 IT-аккр. |
| ФОТ по структуре занятости (ТД / ИП / самозанятые / иное) | P0 payroll reconstruction |
| Ключевые сотрудники: функции, сроки работы, опционы/доли | P2.7 + P4 retention |
| Owner compensation: ЗП + дивиденды + выплаты на связанные ИП | P1.5 + P0 |
| Региональные рыночные ставки ЗП для ключевых ролей (если есть бенчмарк) | P0 payroll reconstruction reference |

**Workstream 6: 152-ФЗ / ПДн / КИИ**

| Документ | Why |
|---|---|
| Регистрация оператора ПДн в РКН | P3 |
| Реестр обрабатываемых ПДн + правовые основания | P3 |
| Договоры поручения на обработку с клиентами (если хостит их ПДн) | P3 |
| Если есть гос-клиенты — лицензии ФСТЭК/ФСБ | P3 КИИ |
| Уведомления / штрафы РКН за 3 года | P3 historical risk |

**Workstream 7: Активы и лицензии**

| Документ | Why |
|---|---|
| Реестр оборудования с принадлежностью (на ком оформлено) | P2.8 |
| Лицензии ПО: на ком оформлены, передаваемые ли | P2.8 |
| Товарные знаки, домены, права на код / методологии | P2.8 |
| Договоры аренды офиса и оборудования | P2.8 + P0 cost allocation |

**Workstream 8: Юр-DD**

| Документ | Why |
|---|---|
| Арбитражные дела за 3 года (kad.arbitr.ru / Rusprofile) | P4 + risk overview |
| Исполнительные производства | Rusprofile pull |
| Судебные споры с сотрудниками | P4 retention risk |
| Подписанные NDA с клиентами / ограничения раскрытия | DD workflow |

### Step 3: Status tracking + escalation

Status: `Not Started → Requested → Received → In Review → Complete → Red Flag → Refused`

`Refused` — продавец отказал. Если документ имеет `priority: P0` и `Refused` — автоматический red flag в P7 escalation router.

### Step 4: Integration с seller-feedback-draft (P6.5)

Каждая строка чек-листа со статусом `Requested` / `Not Started` имеет `catalog_id` из [SELLER_FOLLOWUP_CATALOG.md](../../../../../SELLER_FOLLOWUP_CATALOG.md). При генерации письма продавцу P6.5 берёт формулировки оттуда, не сочиняет ad-hoc.

Если для пункта `catalog_id: missing` — задача добавить его в каталог перед использованием.

### Step 5: Output

- `deals/<target>/checklist.md` — основной артефакт (живой документ)
- Сводный dashboard блок во frontmatter `PORTRAIT.md`:

```yaml
dd_checklist:
  total_items: 47
  received: 22
  in_review: 8
  red_flags: 3
  refused: 1
  completion_pct: 47
  blocking_for_p0: ["ОСВ по контрагентам TARGET-B"]
  blocking_for_p1: ["Перечень ИП-сотрудников"]
```

## Sector-specific additions (для ИТ-аутсорса)

Уже встроены в workstream-ы 6/7. Дополнительно:
- Если таргет работает с банками — добавить блок 161-ФЗ / Положение 757-П (требования к ИБ)
- Если таргет работает с медициной — 323-ФЗ (медтайна, отдельный режим ПДн категории «специальные»)
- Если у таргета есть SaaS-продукт (не только аутсорс) — добавить из апстрима `software/SaaS` блок (cohorts, hosting, churn)

## Failure modes & guardrails

- **Не запрашивать всё сразу.** P0-приоритеты — первой волной (10-15 пунктов). Остальное — после первого ответа продавца.
- **Каждый запрос имеет `why`.** Это входит в P6.5: «без X нельзя подтвердить Y», не «пришлите ещё всё».
- **Если продавец `Refused` на любой `priority: P0`** — это сигнал. Не блокировать пайплайн, но явно отметить в P7 escalation.
- **Не дублировать запросы.** Если документ покрывает несколько `needed_for` — одна строка, multiple needed_for.

## Связанные скиллы

- **Producer:** этот скилл (на старте сделки)
- **Consumers:** все P0-P7 (используют `received` документы)
- **Tight coupling:** P6.5 `ru-seller-feedback-draft` (генерирует письма из `Requested` / `Refused` пунктов)
- **Cross-ref:** [SELLER_FOLLOWUP_CATALOG.md](../../../../../SELLER_FOLLOWUP_CATALOG.md) — каталог формулировок
