# Baseline Findings — апстрим `dd-checklist` на РФ-данных

Этап 1 из [RU_ADAPTATION_PLAN.md](RU_ADAPTATION_PLAN.md). Цель — зафиксировать, что апстримный `private-equity/dd-checklist` пропускает / перевирает / неприменимо на типовом пакете документов от РФ-таргета (`test-data/_overlay_test/`), чтобы последующие РФ-скиллы (P0–P7) били по реальным пробелам, а не по предположениям.

## Что в тест-пакете

| Файл | Что внутри |
|---|---|
| Бухотчётность 2023/2024/2025 (TARGET-A + TARGET-B) | РСБУ формы 1/2 (баланс + ОПУ), 2 юрлица × 3 года |
| Отчёт по выручке 2022-2025 по направлениям | Управ.учёт: разрез по направлениям (1С, аутсорс, оборудование, аренда) |
| Отчёт по выручке/ср.чек 2023-2025 | Помесячно, ср.чек по клиентам |
| Распределение расходов | Методология аллокации общих расходов (вкл. зарплату руководителя) |
| Учёт (ОПиУ) 2024-2026 | Управленческий ОПиУ с прогнозом |
| Финмодель 2025-2027 | Модель окупаемости с допущениями + чувствительность |
| seed.json | Маппинг анонимизации (TARGET-A / TARGET-B / TARGET-A-GROUP) |

Структурные особенности (типовые для МСБ ИТ-аутсорса) — 2 юрлица в группе, recurring + one-time перемешаны, owner compensation размазана в «общих», помесячная рентабельность волатильна, псевдонимы `LOC-XXX` в управ.данных неразличимы анонимайзером.

---

## Workstream 1: Financial DD

Апстрим просит: QoE, working capital, debt, capex (maintenance vs growth), tax structure, audit history, pro forma adjustments.

| Пункт апстрима | Что произойдёт на наших данных | Класс |
|---|---|---|
| **QoE (Quality of Earnings)** | Посчитает EBITDA по управ.ОПиУ как есть. **Не увидит**, что 10–12 «сотрудников» — ИП на УСН 6%, что часть выручки идёт через связанное юрлицо (TARGET-B), что в «общих расходах» сидит owner comp. **Заявленная EBITDA ≠ post-deal EBITDA.** | ❌ **MISS — критично** (покрывает P0 `ru-whitening-math`) |
| **Working capital** | Generic-анализ NWC. **Не покроет** практику АВЕ+Фомичева: aging кредиторки/дебиторки, концентрация по поставщикам/клиентам, связанные стороны, скрытые займы от учредителей. | ⚠️ **WEAK** (покрывает усиленный P5) |
| **Debt and debt-like items** | Спросит про term loans, revolver. **Неприменимо как сформулировано** — у МСБ скорее займы от учредителей, лизинг, кредиторка перед связанными ИП. | ⚠️ **REFRAME** |
| **Capex maintenance vs growth** | Для аутсорса сисадминов — оборудование часто на ИП собственника. Апстрим **не задаст вопрос** «на ком оформлены лицензии и железо». | ❌ **MISS** (покрывает P2.8 `ru-asset-inventory`) |
| **Tax structure** | Спросит про federal/state, transfer pricing, NOLs. **Полностью US-centric, неприменимо.** Не покроет: УСН-лимиты, 54.1 НК (ИП-схема), дробление, ИТ-льготы Минцифры, НДС 22% с 2026, конверты. | ❌ **MISS — критично** (покрывает P1 `ru-tax-risk-scan` + P2 `ru-it-accreditation-check`) |
| **Audit history** | Спросит про Big-4 audited financials. У МСБ их обычно нет — есть РСБУ + управ. **Неприменимо.** | ⚠️ **REFRAME → P5 `ru-financial-audit-rsbu`** + P2.5 mgmt-vs-rsbu recon |
| **Pro forma adjustments** | Generic synergies. **Не учтёт whitening adjustment** как обязательный pro forma. | ❌ **MISS** (часть P0) |

**Главный финансовый пробел:** апстрим оперирует понятиями GAAP-аудита, у нас — два юрлица на УСН с управленческим ОПиУ и формами 1/2 РСБУ. Все «pro forma» должны идти через whitening, иначе EBITDA — мираж.

---

## Workstream 2: Commercial DD

| Пункт апстрима | Что произойдёт | Класс |
|---|---|---|
| TAM/SAM/SOM, market share | Для МСБ ИТ-аутсорса сисадминов в регионе РФ публичных market sizing-данных нет. **Неприменимо в текущем виде.** | ❌ **INAPPLICABLE** |
| **Customer concentration, retention, NPS** | Концентрация — посчитает (если дать список клиентов). **Retention** — без когорт по recurring (1С:ИТС / ИТС / обслуживание) не разделит. NPS у МСБ обычно отсутствует. | ⚠️ **PARTIAL** (покрывает P1.8 `ru-client-base-quality`) |
| Pricing power, contract structure | **Не задаст вопрос** про change-of-control в РФ-договорах — критично, т.к. многие контракты содержат пункт о смене бенефициара. | ❌ **MISS** (покрывает P4 `ru-spa-risks` + customer base) |
| Sales pipeline, backlog | МСБ редко ведёт pipeline. **Применимо**, но низкого качества данных. | ⚠️ **WEAK** |

**Главный коммерческий пробел:** апстрим не различает recurring (1С:ИТС, 1С:ФРЕШ, обслуживание) vs one-time (оборудование, разовые внедрения), а это **базовый драйвер мультипликатора оценки** ИТ-аутсорса. Нужен P1.5 `ru-revenue-by-direction`.

---

## Workstream 3: Legal DD

| Пункт апстрима | Что произойдёт | Класс |
|---|---|---|
| Corporate structure, org chart | **Не запросит ЕГРЮЛ-выписки на все юрлица группы + ИНН учредителей** → не построит граф аффилированных. | ❌ **MISS** (покрывает Rusprofile-enrich + P0.5 multi-entity) |
| Material contracts | Generic-вопросы. **Не спросит** про change-of-control под РФ-право, про лицензии ПО оформленные на собственника. | ⚠️ **REFRAME** |
| Litigation history | По US-PACER не подойдёт. **Неприменимо без kad.arbitr.ru / Rusprofile.** | ❌ **MISS** (через Rusprofile-pull) |
| IP portfolio | Для ИТ-аутсорса IP минимален. **Применимо** в усечённом виде. | ✓ **OK** |
| **Regulatory compliance** | Спросит про SOX, FCPA, GDPR. **Полностью неприменимо.** Нужно: 152-ФЗ (ПДн), 187-ФЗ (КИИ), лицензии ФСТЭК/ФСБ для гос-клиентов, аккредитация Минцифры. | ❌ **MISS — критично** (покрывает P2 + P3) |
| Employment, non-competes | Апстрим спрашивает про non-compete. В РФ non-compete для собственника — только ст. 1033 ГК на договорной основе. **Перевирает практику.** | ❌ **WRONG** (покрывает P4 `ru-spa-risks`) |

---

## Workstream 4: Operational DD

| Пункт апстрима | Что произойдёт | Класс |
|---|---|---|
| **Management assessment, key person risk** | Generic-вопрос «зависит ли бизнес от founder?». **Не сделает** owner dependency model: cash extraction + operational role + replaceability cost + 4 сценария (A/B/C/D). | ❌ **MISS** (покрывает P2.7 `ru-owner-dependency-model`) |
| Org structure | Спросит схему. **Не выявит** оформленных как ИП «сотрудников» — это самый часто скрываемый артефакт. | ❌ **MISS** (вход в P1) |
| IT systems | Для самого ИТ-аутсорса вопросы про их собственный IT — релевантны, но низкоприоритетны. | ✓ **OK low-pri** |
| Supply chain | Для услуг — про вендоров (1С, Microsoft, …) и лицензии. **Реальный риск** — на ком оформлены лицензии партнёров. | ⚠️ **REFRAME → P2.8** |
| Insurance | МСБ обычно минимум. **Применимо**, низкого приоритета. | ✓ **OK low-pri** |

---

## Workstream 5: HR / People

| Пункт апстрима | Что произойдёт | Класс |
|---|---|---|
| Org chart, headcount | Если запросит — увидит «10 человек». **Не сравнит** с среднесписочной из Rusprofile, не выявит ИП/самозанятых вне штата. | ❌ **MISS** (покрывает P1 + Rusprofile-enrich) |
| Compensation benchmarking | US-данные. **Неприменимо.** Нужны региональные ставки сисадминов. | ⚠️ **REFRAME** |
| Benefits, pensions | В РФ это страховые взносы 30% (или 7.6% для ИТ-аккр.). **Логика другая** — это не benefits, это налоговая нагрузка. | ❌ **WRONG framing** (часть P0 whitening + P2) |
| Key employee retention | Generic. **Не учтёт** РФ-специфику: bonus в SPA как retention, conditional escrow, ст. 1033 ГК non-compete. | ⚠️ **REFRAME → P4** |
| Union/labor | Неприменимо в РФ-МСБ. | ❌ **INAPPLICABLE** |

---

## Workstream 6: IT/Tech DD (для tech-enabled)

| Пункт апстрима | Что произойдёт | Класс |
|---|---|---|
| Tech stack, technical debt | Релевантно. | ✓ **OK** |
| Cybersecurity | Generic. Не покроет 187-ФЗ КИИ. | ⚠️ **REFRAME → P3** |
| **Data privacy** | Спросит про GDPR/CCPA/SOC2. **Полностью неприменимо.** Нужно 152-ФЗ + регистрация в РКН + договоры поручения на обработку ПДн. | ❌ **WRONG** (покрывает P3 `ru-152fz-check`) |

---

## Что апстрим вообще НЕ запрашивает (структурные пробелы)

1. **Финмодель продавца** как объект анализа. Апстрим обращается с финмоделью как с справкой. Нам нужно её **переиграть** на белых параметрах (`ru-finmodel-rewrite`, часть P0).
2. **Распределение общих расходов** (отдельный артефакт у нашего таргета). Owner comp размазан — апстрим не вытащит. P1.5 `ru-cost-allocation-audit`.
3. **Multi-entity reconciliation.** Апстрим работает с одной target entity. У нас 2 юрлица минимум — без сверки whitening невозможен. P0.5.
4. **Помесячная аномалия.** Апстрим работает с годовыми. У нас есть помесячный ОПиУ с провалами (отриц.рентабельность Q1). P3.5 `ru-monthly-anomaly`.
5. **Valuation basis extract.** На чём продавец строит цену (payback N лет / мультипликатор EBITDA / мультипликатор выручки) — апстрим не вытаскивает структурированно. P1.7.
6. **Seller feedback draft + outbound pack.** Апстрим выдаёт checklist, не письмо. P6.5 + P6.7.
7. **Escalation routing (Tier 1/2/3).** Апстрим выдаёт report, не routing-решение. P7.

---

## Что апстрима достаточно (use as-is или с минимальной редактурой)

- Структура status tracking (Step 3) — переиспользуем.
- Red flag summary формат (Step 4) — переиспользуем, добавив `impact_rub` и привязку к секциям РФ-отчёта.
- Sector-specific additions — паттерн полезен, но контент полностью заменить.
- Step 5 output — Excel заменяем на MD (см. `ru-md-report-builder` P6).

---

## Сводная таблица: пробел → покрывающий РФ-скилл

| Пробел | Скилл из плана |
|---|---|
| GAAP-аудит вместо РСБУ + управ | P5 `ru-financial-audit-rsbu` + P2.5 `ru-mgmt-vs-rsbu-recon` |
| QoE без whitening | **P0 `ru-whitening-math`** |
| US tax structure | P1 `ru-tax-risk-scan` + P2 `ru-it-accreditation-check` |
| GDPR вместо 152-ФЗ | P3 `ru-152fz-check` |
| Одна entity вместо группы | P0.5 `ru-multi-entity-recon` |
| Generic customer concentration | P1.8 `ru-client-base-quality` |
| Recurring vs one-time не разделено | P1.5 `ru-revenue-by-direction` |
| Активы и лицензии — не на покупаемой entity | P2.8 `ru-asset-inventory` |
| Working capital поверхностно | усиленный P5 (под-блок АВЕ+Фомичева) |
| Owner dependency generic | P2.7 `ru-owner-dependency-model` |
| Valuation basis не вытащен | P1.7 `ru-valuation-basis-extract` |
| US SPA: non-compete, indemnity | P4 `ru-spa-risks` |
| Нет внешнего обогащения | Rusprofile-enrich (P0.7) |
| Нет помесячного среза | P3.5 `ru-monthly-anomaly` |
| Нет письма продавцу | P6.5 `ru-seller-feedback-draft` |
| Нет outbound pack | P6.7 `ru-seller-deliverable-pack` |
| Нет routing-решения | P7 `ru-escalation-router` |
| Финмодель не переигрывается | `ru-finmodel-rewrite` (часть P0) |

**Покрытие:** все идентифицированные пробелы маппятся на запланированные скиллы. **Новых пробелов, не учтённых в плане, не выявлено.** План структурно полон.

---

## Решение / next step

Этап 1 закрыт. Идём в **Этап 0.5 — multi-entity recon** (1–2 дня) как пререкивизит к P0, ИЛИ сразу в **Этап 2 — P0 `ru-whitening-math`** на одном юрлице.

План явно говорит: «без multi-entity whitening невозможен». Рекомендация — Этап 0.5 первым.
