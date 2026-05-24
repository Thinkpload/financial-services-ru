# Seller follow-up catalog — IT-аутсорс сисадминов

Каталог типовых follow-up артефактов, которые мы запрашиваем у продавца при DD ИТ-аутсорсера. LLM (P6.5 `ru-seller-feedback-draft`) выбирает из этого списка **по ID**, а не сочиняет формулировки с нуля — это даёт сопоставимость между сделками и накапливает опыт практики.

- **Используется в:** [PIPELINE_SCHEMA.md](PIPELINE_SCHEMA.md) — поле `seller_feedback_draft.requested_followups[].catalog_id`.
- **Методология:** [RU_ADAPTATION_PLAN.md](RU_ADAPTATION_PLAN.md) — секция «Методология первичного анализа».
- **Принцип:** каждый запрос имеет `rationale` (какой вывод без этого невозможен) и `confirms` (что именно подтверждает) — это перехватывает антипаттерн «пришлите ещё всё».

## Формат записи

```yaml
- id: <stable kebab-case ID>
  title: <короткое название для оператора>
  ask_phrasing_ru: <формулировка для письма продавцу, в кавычках>
  artifact_type: spreadsheet | document | extract_1c | contract_copy
                | registry | screenshot | narrative
  confirms: <какой вывод мы можем закрыть, получив это>
  unblocks_skill: <P-номер скилла, который заблокирован без этого>
  typical_format: <формат, в каком обычно приходит>
  sensitivity: low | medium | high       # насколько чувствительно для продавца отдавать
  alternative_if_refused: <фолбэк, если продавец не даёт>
```

## Каталог

### Финансы и налоги

```yaml
- id: clients_revenue_breakdown
  title: Раскладка выручки по клиентам (услуга → стоимость → периодичность)
  ask_phrasing_ru: |
    Пришлите выгрузку выручки в разрезе клиентов за последние 12 месяцев:
    клиент (можно обезличить как Клиент-1, Клиент-2) → услуга → стоимость
    абонентского платежа / разовых работ → периодичность.
    Формат — Excel, по строке на каждую услугу для каждого клиента.
  artifact_type: spreadsheet
  confirms: top_3/top_5 концентрация, средний чек, recurring revenue split
  unblocks_skill: P1.5 (ru-revenue-by-direction), P1.8 (client_base_assessment.customers[])
  typical_format: Excel, выгрузка из 1С или ручная таблица
  sensitivity: medium
  alternative_if_refused: согласие на обезличенную выгрузку через нашего аналитика под NDA

- id: ltv_export
  title: LTV-выгрузка (дата начала контракта, срок, исторический revenue per client)
  ask_phrasing_ru: |
    Пришлите по каждому действующему клиенту: дату начала договора, текущий срок
    договора, ежемесячный платёж сейчас, суммарную выручку от клиента за всю
    историю отношений. Это позволит нам посчитать LTV и оценить устойчивость базы.
  artifact_type: spreadsheet
  confirms: LTV per client, churn signals, базовая стабильность клиентских отношений
  unblocks_skill: P1.8 (client_base_assessment), P2.8 (assets_inventory.client_base_as_asset)
  typical_format: Excel; если нет — выгрузка из 1С УНФ/ERP с датами договоров
  sensitivity: medium
  alternative_if_refused: хотя бы дата начала + текущий месячный платёж по топ-5

- id: typical_contract_pto
  title: Типовой договор на ПТО (постоянное техническое обслуживание / абонку)
  ask_phrasing_ru: |
    Пришлите типовой договор на абонентское/постоянное техническое обслуживание,
    по которому работаете с большинством клиентов (имя клиента и реквизиты можно
    замазать). Нам важны: предмет, объём услуг, цена, срок, change-of-control
    оговорки, ответственность.
  artifact_type: contract_copy
  confirms: change-of-control риски, transferability клиентской базы, SLA-структура
  unblocks_skill: P6 (change-of-control сканер), P1.8 (transferability_per_client)
  typical_format: PDF / DOCX
  sensitivity: low
  alternative_if_refused: краткое описание условий + 1-2 ключевых пункта в формулировках

- id: osv_1c_last_year
  title: ОСВ (оборотно-сальдовая ведомость) из 1С за последний год
  ask_phrasing_ru: |
    Пришлите ОСВ по всем счетам за последний закрытый год — в формате выгрузки
    из 1С (Excel). Это позволит нам увидеть реальные потоки по контрагентам,
    а не только агрегаты.
  artifact_type: extract_1c
  confirms: внутригрупповые потоки, аффилированные сделки, реальная контрагентская сеть
  unblocks_skill: P0.5 (ru-multi-entity-recon), P5 (ru-financial-audit-rsbu)
  typical_format: Excel из 1С с типовой структурой ОСВ
  sensitivity: high
  alternative_if_refused: ОСВ по счетам 60/62/76 (контрагенты) под NDA, без остальных

- id: staff_schedule_employment_mix
  title: Штатное расписание + структура занятости (ТД / ИП / самозанятые)
  ask_phrasing_ru: |
    Пришлите штатное расписание + список всех людей, фактически работающих в
    компании, с указанием формы оформления: трудовой договор, ИП, самозанятый,
    привлекаемый подрядчик. Имена можно обезличить (Сотрудник-1, Сотрудник-2).
  artifact_type: spreadsheet
  confirms: 54.1 риск, реальный ФОТ для whitening, owner role indicators
  unblocks_skill: P0 (ru-whitening-math), P1 (ru-tax-risk-scan), P2.7 (ru-owner-dependency-model)
  typical_format: Excel
  sensitivity: high
  alternative_if_refused: агрегаты — сколько ТД vs сколько ИП vs сколько самозанятых, без детализации
```

### Активы

```yaml
- id: hardware_asset_list
  title: Список оборудования на балансе и в эксплуатации
  ask_phrasing_ru: |
    Пришлите список оборудования: серверы, ноутбуки сотрудников, сетевое
    оборудование, оборудование, размещённое у клиентов. По каждой позиции:
    наименование, год покупки, балансовая стоимость, на чьём балансе (юрлицо,
    ИП собственника, физлицо), где физически находится.
  artifact_type: spreadsheet
  confirms: что реально переходит в сделку vs остаётся у продавца, замаскированный leasing
  unblocks_skill: P2.8 (assets_inventory.hardware)
  typical_format: Excel; для основных средств — из 1С (счёт 01)
  sensitivity: low
  alternative_if_refused: хотя бы список «что критично для работы и где это сейчас»

- id: software_licenses_registry
  title: Реестр лицензий ПО (на ком оформлены)
  ask_phrasing_ru: |
    Пришлите реестр всех используемых лицензий: 1С, Microsoft, антивирусы,
    специализированный софт. По каждой лицензии: на кого оформлена (юрлицо
    таргета, ИП собственника, клиент), срок, количество, стоимость продления.
  artifact_type: registry
  confirms: лицензии переходят в сделку или требуют перерегистрации, скрытые расходы
  unblocks_skill: P2.8 (assets_inventory.software_licenses)
  typical_format: Excel / выгрузка из системы учёта лицензий
  sensitivity: low
  alternative_if_refused: разговор по верхам — «на ком оформлены ключевые лицензии»

- id: ip_methodologies
  title: Внутренние методологии, инструкции, runbook'и, кодовая база
  ask_phrasing_ru: |
    Опишите, какие внутренние методические материалы, инструкции, скрипты
    автоматизации, runbook'и существуют. Кому принадлежат права (компания /
    собственник / сотрудник). Сами материалы пока показывать не нужно — нам
    важно понять, что вообще есть и кому принадлежит.
  artifact_type: narrative
  confirms: что из IP реально переходит, риск ухода с командой
  unblocks_skill: P2.8 (assets_inventory.ip)
  typical_format: текстовое описание
  sensitivity: medium
  alternative_if_refused: интервью с техлидом / собственником

- id: brand_assets
  title: Доменные имена, сайт, аккаунты в каталогах, маркетинговые ассеты
  ask_phrasing_ru: |
    Пришлите список: домен и на кого зарегистрирован, аккаунты в каталогах
    подрядчиков (Habr Career, профильные площадки), социальные сети, email-домены
    клиентских коммуникаций.
  artifact_type: registry
  confirms: brand assets переходят / остаются у собственника, маркетинговый pipeline
  unblocks_skill: P2.8 (assets_inventory.brand)
  typical_format: текстовый список со скриншотами whois
  sensitivity: low
  alternative_if_refused: проверяется самостоятельно через whois + поиск
```

### Юридическое и операционное

```yaml
- id: top_clients_contracts_readonly
  title: Договоры с топ-5 клиентов на чтение (без копий)
  ask_phrasing_ru: |
    Дайте возможность нашему юристу ознакомиться с действующими договорами
    с топ-5 клиентов — на чтение, без копирования. Проверяем три вещи:
    change-of-control, срок, exclusivity. Имена клиентов можно скрыть.
  artifact_type: contract_copy
  confirms: реальная transferability топ-клиентов, скрытые exclusivity-обязательства
  unblocks_skill: P4 (ru-spa-risks), P1.8 (transferability_per_client)
  typical_format: чтение в офисе продавца / через защищённую комнату
  sensitivity: high
  alternative_if_refused: «отказ от показа договоров топ-клиентов» сам по себе является red flag

- id: related_parties_disclosure
  title: Список аффилированных лиц и связанных юрлиц/ИП
  ask_phrasing_ru: |
    Пришлите перечень всех связанных лиц: ИП собственника и родственников,
    юрлица, где собственник или родственники имеют долю, юрлица, через которые
    проходит выручка/расходы группы. Это нужно для корректной консолидации
    экономики группы.
  artifact_type: spreadsheet
  confirms: признаки дробления, реальные границы группы
  unblocks_skill: P0.5 (ru-multi-entity-recon), P1 (ru-tax-risk-scan)
  typical_format: текстовый список ИНН/ОГРН
  sensitivity: high
  alternative_if_refused: восстанавливается из Rusprofile по учредителям

- id: owner_functions_narrative
  title: Описание роли собственника в операционке
  ask_phrasing_ru: |
    Опишите, что именно вы делаете в компании сейчас в течение типичной недели:
    управление командой, продажи, ключевые клиенты, технические эскалации,
    финансы. Это критично для нас — чтобы понять, что нужно компенсировать
    после сделки.
  artifact_type: narrative
  confirms: owner_dependency.owner_operational_functions, replaceability
  unblocks_skill: P2.7 (ru-owner-dependency-model)
  typical_format: интервью или письменный ответ
  sensitivity: medium
  alternative_if_refused: восстанавливается по косвенным признакам (organigram + интервью с сотрудниками)
```

## Использование в скиллах

**P6.5 `ru-seller-feedback-draft`** при генерации `requested_followups[]`:
1. Анализирует `unresolved_points` и `open_questions` из агрегатора.
2. Для каждого пробела ищет в каталоге запись с подходящим `unblocks_skill` / `confirms`.
3. Берёт `ask_phrasing_ru` как стартовый текст, адаптирует под конкретный контекст (упоминание уже присланных документов).
4. Сохраняет `catalog_id` в `requested_followups[].catalog_id` — это даёт трассировку и накопление статистики «какие запросы чаще всего получают отказ».

**P6.7 `ru-seller-deliverable-pack`** включает этот список как заключительную секцию PDF («Что нужно для следующего шага») с человеческими формулировками + сноска `[CAT:id]` для нашей внутренней трассировки.

## Расширение каталога

Любая новая повторяющаяся формулировка из реальной практики → добавляется как новая запись в этот файл. Принцип: если formula уже использовалась 3+ раза на разных сделках, она становится записью в каталоге. Это превращает индивидуальный опыт в продуктовый актив.
