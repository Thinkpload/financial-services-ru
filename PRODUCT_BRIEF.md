# Product Brief — РФ M&A DD ИТ-аутсорса

Одностраничник: что мы строим, для кого, зачем и как понять, что готово. Если что-то в [RU_ADAPTATION_PLAN.md](RU_ADAPTATION_PLAN.md) противоречит этому брифу — бриф главнее.

## Проблема

Покупатель в белую (ОСНО) хочет покупать малых ИТ-аутсорсеров сисадминов (B2B, МСБ, выручка ≤100 млн ₽/год). Таргеты живут в серой/гибридной схеме: ИП-«сотрудники», дробление по УСН, конверты, лицензии на собственнике. **EBITDA продавца ≠ EBITDA покупателя.** Payback по заявленным цифрам — мираж. Нанять аудитора на каждый таргет (~45k₽/кейс) не сходится при воронке 10–30 сделок в год + скрининг.

## Что мы строим

**LLM-пайплайн, который превращает хаос документов от продавца в стандартную переговорно-пригодную карточку компании (`PORTRAIT.md`).** Не «умный читатель финдоков», а **нормализатор в фиксированную схему** — одинаковую для всех таргетов, чтобы их можно было сравнивать и торговаться.

Ключевая идея: автоматизировать **стандарт анализа**, а не «понимание финансов». Schema first → extraction → normalization → questions → narrative.

## Для кого

Один покупатель (мы сами + внутренний аналитик), 10–30 сделок в год. Не SaaS, не для рынка. Tier 2 (аналитик) и Tier 3 (внешний эксперт) работают **в той же схеме**, что и LLM Tier 1 — это даёт сопоставимость.

## Что на выходе (по одной сделке)

Каталог `deals/<target>/` с:
- **`PORTRAIT.md`** — машинно-агрегируемая карточка (frontmatter + ссылки). Главный артефакт для cross-deal анализа.
- **8 секционных MD-отчётов** (summary, whitening, financial, tax-risks, IT-аккр., 152-ФЗ, SPA, people).
- **Outbound PDF для продавца** — «Executive feedback pack»: что поняли, сильные стороны, вопросы (не обвинения), preliminary valuation range, next steps.
- **Письмо-followup продавцу** — обоснованный запрос недостающего: «без X нельзя подтвердить Y».
- **Escalation decision**: Tier 1 / 2 / 3.

## Главные смысловые слои (что обязательно в карточке)

1. Reliability check (можно ли доверять входу)
2. Valuation basis (на чём продавец строит цену)
3. **Whitening** — пересчёт EBITDA/payback в белую модель (ядро всего)
4. Revenue normalization (направления, recurring vs one-time)
5. Client base quality (per-client LTV, concentration, change-of-control)
6. Assets inventory (transfers / requires_renegotiation / stays_with_seller)
7. Cost structure + owner compensation
7a. **Working capital audit** (практика АВЕ+Фомичева): кредиторка (структура/aging/связанные стороны), дебиторка (полный aging/концентрация/безнадёжная), налоговые задолженности (публичные + признаки спорных), сходимость управ↔бух
8. Owner dependency + 4 сценария «бизнес без основателя»
9. Seller feedback draft (письмо + outbound pack)
10. Escalation routing

## Границы (что НЕ делаем)

- Не tax-law claims — только сигналы.
- Не автономные инвест-решения — решение за человеком.
- Не OCR сканов, не прямой коннект к 1С, не СПАРК/Контур API, не юр-DD арбитража глубоко, не LBO/DCF/comps/3-statement, не партнёрские плагины (LSEG/S&P).
- Не SaaS-продукт для рынка.

## Где живёт код

- **Этот репо (`financial-services-ru`)** — методология, спецификации скиллов, плагины Claude Code, шаблоны Managed Agent.
- **Соседний репо (`GW-Buy-Busineses-Product-IT-Outsource`)** — runtime LLM-пайплайна (там P0–P7 воплощаются в код).
- Анонимайзер (`tools/anonymize/`) — уже работает.

## Definition of Done для пилота

End-to-end прогон на **одной реальной сделке**: документы продавца → анонимизация → Rusprofile-enrich → multi-entity recon → whitening → tax/IT/152-ФЗ/SPA → `PORTRAIT.md` + 8 секций + outbound PDF продавцу + escalation tier. Фидбек от пилота → бэклог.

## Очерёдность реализации (упрощённо)

1. **P0 — whitening** (без него все цифры не те)
2. **P1 — tax-risk-scan** + адаптация `dd-checklist`
3. **P1.7/1.8 — valuation basis + client base**
4. **P2/3 — IT-аккредитация + 152-ФЗ**
5. **P2.7/2.8 — owner dependency + asset inventory**
6. **P4/5 — SPA risks + RSBU audit**
7. **P6/6.5/6.7/7 — MD-репорт + seller feedback + outbound pack + escalation router**
8. **Pilot**

Полный список скиллов, схема выходных данных и этапы — в [RU_ADAPTATION_PLAN.md](RU_ADAPTATION_PLAN.md) и [PIPELINE_SCHEMA.md](PIPELINE_SCHEMA.md).
