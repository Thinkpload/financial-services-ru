---
name: ru-seller-deliverable-pack
description: Generate an outbound PDF "Executive feedback pack" for the seller. Demonstrates expertise — what we understood about the business, strengths, areas_of_concern (reframed as questions not accusations), preliminary_valuation_range (with disclosure flag), next steps. MD→PDF via pandoc, standardized template. internal_only_appendix stays internal as negotiation cards. Triggers on "outbound pack", "deliverable pack", "feedback пакет продавцу", "executive pack", "PDF для продавца".
---

# Seller Deliverable Pack (P6.7)

В РФ-практике МСБ M&A продавец **редко получает содержательную обратную связь** от потенциальных покупателей. Большинство DD-процессов воспринимаются как «дайте ещё документы, дайте ещё…».

Outbound «Executive feedback pack» меняет динамику: показывает экспертизу, демонстрирует серьёзность, даёт продавцу ощущение, что его слушали. **Это инструмент конкуренции за хорошие сделки.**

## When to use

- Завершён первый полный прогон P0-P6 (минимум summary + whitening + tax-risk + client-base + valuation_basis)
- Перед / после первого крупного созвона с продавцом
- В сочетании с P6.5 followup письмом — как value-exchange («мы вам — feedback pack, вы нам — недостающие документы»)

## Inputs

- Frontmatter всех завершённых секций
- `valuation_basis` (P1.7) с counter-offer range
- `client_base_assessment` strengths (P1.8)
- `it_accreditation` если stable (P2) — это strength
- `tax_risk_scan` (P1) — для concerns (но reframed!)
- `owner_dependency.open_questions_for_seller` (P2.7)

## Workflow

### Step 1: Структура pack-а (фиксированная)

```
Executive Feedback Pack — <target_pseudonym>
[1 страница — обложка]

1. Business understanding (что мы поняли)         [1 стр]
2. Strengths (что нам нравится)                    [1 стр]
3. Areas of focus (вопросы, не претензии)          [1-2 стр]
4. Preliminary thoughts on structure               [1 стр]
5. Next steps                                      [полстраницы]

Total: 5-6 страниц PDF.

[Internal-only appendix — не в outbound]
A. Detailed counter-offer range
B. Tax-risk impact monetary estimates
C. Walkaway price
```

### Step 2: Business understanding

Демонстрация того, что мы **разобрались** в их бизнесе. Не выписки из их документов.

```markdown
## Что мы поняли о бизнесе

Группа из 2 юрлиц (TARGET-A + TARGET-B) с консолидированной выручкой ~140 M ₽ за 2024 и сильной recurring-составляющей (~67% от выручки). Основные направления:

- **ИТ-обслуживание** (~45% выручки, recurring) — основной актив. Средний срок отношений с клиентами 4+ года, что для МСБ-аутсорса — выше среднего.
- **1С-направление** (~28% выручки, recurring) — стабильный поток, низкая операционная сложность.
- **Оборудование** (~22% выручки, one-time) — пропускное направление с низкой маржой, но удерживающее клиентов внутри экосистемы.
- **Аренда вычислительных ресурсов** (~5% выручки) — пока экспериментальное.

Управленческий учёт ведётся качественно — это редкость для сегмента и заметный плюс при integration post-deal.
```

### Step 3: Strengths

```markdown
## Сильные стороны бизнеса

- **Recurring revenue 67%** — это вверху квартиля для МСБ ИТ-аутсорса в РФ. Прогнозируемость потока.
- **Низкая ротация топ-клиентов** — средний срок отношений 4+ года, что облегчает modeling forward.
- **Управ.учёт развёрнут** — есть методология распределения общих расходов, что сильно ускоряет DD.
- **ИТ-аккредитация Минцифры (если есть и stable)** — налоговые льготы дают существенную экономию в long-run.
- **Низкая зависимость от государственных клиентов** — снижает регулятивный риск.
```

### Step 4: Areas of focus (вопросы, не претензии)

**Критическое правило:** все concerns переформулированы в **вопросы для обсуждения**, не в обвинения.

```markdown
## Области, которые хотим обсудить

### 1. Структура занятости и переход на единую модель
Часть команды оформлена через ИП/самозанятых — это нормальная практика МСБ. Покупатель работает в ОСНО-модели, поэтому хотим обсудить переходный план: как технически и юридически выстроить переход на единый формат, чтобы это было плавно для команды и не повлияло на сервис клиентам.

### 2. Структура группы
Видим 2 юрлица в группе. Хотим понять историческую логику разделения и как сохранить операционную преемственность после consolidation.

### 3. Готовность собственника остаться в transition period
В МСБ-сделках типично 6-18 мес transition. Какой формат был бы комфортен — full-time / part-time / консультант? Это влияет на структуру retention.

### 4. Топ-3 клиента и change-of-control
В договорах с топ-клиентами обычно есть оговорки о смене бенефициара. Хотим обсудить strategy получения consents pre-close — это снижает риск для обеих сторон.
```

**ЗАМЕТЬТЕ:** ни одного слова «whitening gap», «дробление», «54.1 НК», «конверты». Эти темы — internal_only_appendix, не для outbound.

### Step 5: Preliminary thoughts on structure

```markdown
## Предварительные мысли о структуре

На текущем уровне понимания, мы видим:
- **Цена:** диапазон M-N M ₽ — зависит от ответов на вопросы выше и финального DD-результата
- **Структура:** комбинация cash + escrow (3 года) + retention bonus для собственника и 2-3 ключевых сотрудников
- **Timeline:** при текущей динамике — LOI через 4-6 недель, closing через 3-4 месяца после LOI

Мы готовы детально обсудить как только закроем оставшиеся технические вопросы (см. отдельный список).
```

**Critical:** ценовой диапазон — **раскрытие частичное**. `internal_only_appendix.counter_offer_range` содержит low/base/high; в outbound — только base ± 10% или вообще без чисел при первом pack.

`disclosure_flag` (явное решение):
- `disclose_none` — никаких чисел в outbound (для ранней стадии)
- `disclose_base_only` — только base ± narrow
- `disclose_range` — low до base
- `disclose_full` — редко, только после второй итерации

### Step 6: Next steps

```markdown
## Следующие шаги

1. Получить ответы на вопросы из followup letter (отправлено отдельно)
2. Звонок продолжительностью 60-90 мин для обсуждения areas_of_focus
3. После закрытия открытых вопросов — preliminary term sheet
4. Готовы к посещению офиса при необходимости
```

### Step 7: Internal-only appendix (НЕ в outbound)

Остаётся у нас как переговорные карты:

```markdown
## A. Detailed counter-offer range [INTERNAL ONLY]

| Сценарий | Cash | Escrow | Retention | Total | Walkaway? |
|---|---|---|---|---|---|
| Aggressive | 22M | 8M | 4M | 34M | no |
| Base | 28M | 10M | 5M | 43M | no |
| Generous | 32M | 12M | 6M | 50M | yes (>50 walkaway) |

## B. Tax-risk monetary estimates [INTERNAL ONLY]

| Категория | Base impact | Used in indemnity sizing? |
|---|---|---|
| Дробление | 8.5M | yes (cap 12M) |
| 54.1 ИП-схема | 4.2M | yes |
| ... | ... | ... |

## C. Negotiation cards [INTERNAL ONLY]

- Если продавец настаивает на >50M — walkaway, есть 3 альтернативных таргета в pipeline
- Если продавец готов на retention 18 мес — добавляем +3M к base
- Если продавец отказывается от ОСВ → флаг, осторожно с pre-LOI
```

### Step 8: Output

- `deals/<target>/outbound/pack_YYYY-MM-DD_v<N>.md` — версионированный outbound (анонимизированный)
- `deals/<target>/outbound/pack_YYYY-MM-DD_v<N>.pdf` — pandoc render (то, что отправляем)
- `deals/<target>/outbound/internal_appendix_v<N>.md` — internal-only, gitignored if contains real numbers
- Frontmatter:

```yaml
seller_deliverable_pack:
  version: v2
  generated_date: 2026-05-24
  disclosure_flag: disclose_base_only
  pdf_sent_date: null
  pdf_sha: ...
```

### Step 9: Format / branding

- Pandoc template (`templates/outbound_pack.tex` или html, ссылка на template в скилле)
- Без перегруза дизайном — clean, professional
- На обложке: «Подготовлено для обсуждения. Этот документ не является публичной офертой, не раскрывает proprietary методологию.»

## Output contract

См. [PIPELINE_SCHEMA.md](../../../../../PIPELINE_SCHEMA.md), объект `SellerDeliverablePack`. Producer финального PDF. Consumer: продавец (вне пайплайна). Внутренний consumer: P6.5 (включает ссылку на pack в followup).

## Failure modes & guardrails

- **Никакой негативной риторики.** «Risk», «нарушение», «дробление» — не появляются. Эти темы переформулированы.
- **Никаких реальных имён клиентов** в outbound даже если pack идёт назад тому же продавцу. Псевдонимы единые с DD.
- **Disclosure flag — явное решение, не дефолт.** Default `disclose_none` для первого pack.
- **Internal_appendix — gitignored если содержит real numbers.** Только template коммитим.
- **`walkaway_price` никогда не в outbound.** Это всегда internal.
- **Подписант указан явно.** Это не безличный документ.

## Связанные скиллы

- **Prerequisites:** P0, P1, P1.7, P1.8, P2, P2.7 (минимум для содержательного pack)
- **Tightly coupled with:** P6.5 (followup letter часто включает pack)
- **Cross-ref:** P4 (структура SPA из preliminary thoughts on structure)
