---
name: ru-seller-feedback-draft
description: Draft a substantive followup letter to the seller — what was analyzed, what conclusions are emerging, which numbers need clarification, which next document is needed AND WHY (not "send us everything", but "without X we cannot confirm Y"). Pulls phrasings from SELLER_FOLLOWUP_CATALOG.md by catalog_id rather than ad-hoc — accumulates practice. Intercepts the "endless document requests without substantive feedback" failure mode. Triggers on "seller followup", "письмо продавцу", "запрос документов", "what to ask seller", "seller feedback".
---

# Seller Feedback Draft (P6.5)

Типичная anti-pattern: продавец прислал документы → покупатель просит ещё → продавец прислал ещё → … 6 итераций без содержательной обратной связи. Продавец теряет доверие, сделка остывает.

Этот скилл генерирует **обоснованное** письмо: «вот что мы проанализировали, вот выводы, вот что мешает закрыть открытые вопросы — нужен документ X **потому что** Y».

Формулировки запросов — из [SELLER_FOLLOWUP_CATALOG.md](../../../../../SELLER_FOLLOWUP_CATALOG.md) по `catalog_id`, не сочиняются ad-hoc.

## When to use

- После каждого крупного обновления входов (новый документ → re-run пайплайна → новый followup)
- Когда checklist.md имеет несколько пунктов в `Requested` / `Not Started` после прохода P0-P5
- Перед запросом эскалации в Tier 2 (часто Tier 2 не нужен если запросить правильный документ продавцу)

## Inputs

- `checklist.md` (P-dd-checklist) — текущий статус документов
- Frontmatter всех завершённых секций (для «что уже поняли»)
- [SELLER_FOLLOWUP_CATALOG.md](../../../../../SELLER_FOLLOWUP_CATALOG.md) — lookup для формулировок
- Открытые вопросы из P2.7 (`owner_dependency.open_questions_for_seller`)
- Confidence-low блоки из всех секций — там часто нужны добавочные данные

## Workflow

### Step 1: Inventory открытых пунктов

Собрать:
1. Чек-лист items со status: `Not Started`, `Requested`, `Refused`
2. Confidence-low блоки из всех frontmatter (если `confidence: low` → нужен дополнительный input)
3. `open_questions_for_seller` из P2.7
4. `blockers_for_p0_whitening` и аналогичные блокеры из других секций

### Step 2: Приоритизация

Каждый item получает:
- `priority`: P0 / P1 / P2 (= blocking какой стадии анализа)
- `needed_for`: какой downstream скилл требует
- `blocking_decision`: какое решение нельзя принять без этого

**Письмо не должно содержать больше 5-7 запросов за раз.** Если больше — отсечь по `priority`.

### Step 3: Lookup formулировок в catalog

Для каждого запроса — `catalog_id` из SELLER_FOLLOWUP_CATALOG.md. Если `catalog_id: missing` — задача добавить в catalog перед использованием. (Не сочиняем ad-hoc.)

Формат каталога (пример):

```yaml
- catalog_id: structure_of_employment
  why: "Без понимания структуры занятости (ТД / ИП / самозанятые) невозможно посчитать post-deal payroll и оценить риск 54.1 НК"
  request_template: |
    Уточните, пожалуйста, текущую структуру занятости в группе:
    - Количество сотрудников по ТД (с разбивкой по позициям)
    - Список ИП-контрагентов с указанием функций (без раскрытия имён можно)
    - Список самозанятых-подрядчиков
  format_expected: "Excel или PDF, любой удобный вид"
  what_we_will_do_with_it: "Пересчитаем модель ФОТ с учётом перехода на единый формат после сделки — это даст реалистичную post-deal EBITDA"
```

### Step 4: Структура письма

```markdown
# Followup письмо продавцу (draft)

## Что проанализировали

За прошлую неделю по присланным документам:
- Бухотчётность за 3 года по 2 юрлицам — сверка форм 1/2 — расхождений критичных не нашли
- Управ.ОПиУ — определили среднюю маржу по направлениям: ИТ-обслуживание ~28%, 1С-направление ~22%, оборудование ~8%
- Финмодель — переиграли на белых параметрах (страховые 30%, ОСНО)

## Предварительные выводы

- Бизнес устойчив на recurring-выручке (~67% от total)
- Топ-3 клиента дают 41% выручки — типичная концентрация для МСБ-ИТ-аутсорса
- Whitening adjustment даёт пересчитанный EBITDA в диапазоне X-Y M ₽ (vs заявленный Z M ₽). Это не претензия — это техническая разница, неизбежная при переходе на ОСНО

**Чтобы продвинуться к LOI, нам нужно закрыть несколько технических вопросов:**

## Запросы

### 1. [Priority P0] Структура занятости
[формулировка из catalog: structure_of_employment]

**Без этого:** не можем подтвердить post-deal EBITDA, и любая обсуждаемая цена будет приблизительной.

### 2. [Priority P0] ОСВ по контрагентам за 2025 год по обоим юрлицам
[формулировка из catalog: osv_counterparties]

**Без этого:** не можем подтвердить независимость TARGET-A и TARGET-B и оценить риск ФНС переквалификации как дробления.

### 3. [Priority P1] Договоры с топ-3 клиентами (на чтение)
[формулировка из catalog: top_client_contracts]

**Без этого:** не можем оценить риск change-of-control при смене бенефициара — это влияет на структуру SPA и retention conditions.

## Что мы готовы предоставить взамен

- Краткий feedback pack (3-4 страницы) с тем, что мы поняли о бизнесе и нашими предварительными мыслями о структуре сделки (см. P6.7)
- График созвона на этой неделе для обсуждения [open questions из owner-dependency]

## Тайминг

Если получим документы до пятницы — следующая встреча с готовым preliminary structure в течение 10 рабочих дней.

---

**Подписант:** [имя]
**Дата:** [дата]
**Версия письма:** v3 (предыдущие — v1, v2)
```

### Step 5: Output

- `deals/<target>/followups/YYYY-MM-DD_v<N>.md` — версионированный архив писем
- `deals/<target>/followups/latest.md` — symlink/копия на последний
- Update `checklist.md`: статус `Requested` для отправленных, дата отправки
- Frontmatter блок в PORTRAIT.md:

```yaml
seller_communications:
  followups_sent: 3
  latest_sent_date: 2026-05-24
  open_requests_count: 5
  catalog_ids_pending: ["structure_of_employment", "osv_counterparties", "top_client_contracts"]
```

## Output contract

См. [PIPELINE_SCHEMA.md](../../../../../PIPELINE_SCHEMA.md), объект `SellerCommunicationsState`. **Consumers:** P6.7 (outbound pack — синхронизировать message), P7 (если followup отправлен N раз и Refused → escalate), `checklist.md` (status updates).

## Failure modes & guardrails

- **Никогда не запрашивать без `why`.** «Без X не можем подтвердить Y». Иначе продавец чувствует bureaucratic harassment.
- **Никогда не отправлять больше 5-7 запросов за раз.** Если больше — пересортировать по priority, отрезать P2.
- **Не использовать ad-hoc формулировки.** Если для блока нет catalog_id — добавить в catalog первым (это инвариант).
- **«Что мы поняли» — обязательная секция.** Без неё письмо = бюрократическое требование, не диалог.
- **Тон — equal partner, не interrogation.** Продавец = деловой партнёр.
- **Версионирование писем** — позволяет восстановить, какие выводы делали в момент написания (поддерживает chronicle.jsonl из Addendum).

## Связанные скиллы

- **Hard dependency:** [SELLER_FOLLOWUP_CATALOG.md](../../../../../SELLER_FOLLOWUP_CATALOG.md) (lookup table)
- **Prerequisites:** все P0-P5 + dd-checklist
- **Coupled with:** P6.7 (outbound pack — outbound pack часто включается в followup как value-exchange)
- **Downstream:** P7 (escalation if seller refuses repeatedly)
