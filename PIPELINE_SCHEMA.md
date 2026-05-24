# Pipeline output schema — M&A financial pre-analysis

Контракт данных для LLM-пайплайна первичного анализа таргетов. Не план, не методология — **спецификация структур, которые скиллы должны производить**.

- **Методология и обоснование:** [RU_ADAPTATION_PLAN.md](RU_ADAPTATION_PLAN.md), секция «Методология первичного анализа».
- **Реализация:** репо `C:\Users\gllex\_DEV_PROJECTS_2026\GW-Buy-Busineses-Product-IT-Outsource`.
- **Жанр:** этот файл — API-контракт. Изменения здесь влияют на формат выводов всех скиллов P0–P7 и на агрегатор `TargetFinancialAssessment`.

## Главный принцип

Пайплайн строит **`NormalizedTargetProfile`** — стандартизированную карточку, по которой можно сравнивать любых таргетов и вести торг. LLM = исполнитель стандарта, не «умный читатель».

Order of operations:
1. ingest raw → inventory document types
2. extract evidence into structured fields
3. mark uncertainty field-by-field
4. only then produce narrative summaries

Narrative — побочный продукт. Schema — первичный.

## Non-objectives (что не строим)

Это явно **не** входит в задачу пайплайна:

- **Definitive valuation.** Цена сделки не выходит из LLM; пайплайн только готовит базу для торга.
- **Tax-law certainty claims.** Признаки оптимизации помечаются как сигналы, не как юридические выводы.
- **Fully autonomous investment decisioning.** Решение «брать/не брать» — за человеком.

Если фича не помогает screening / normalization / negotiation-support → она не входит в scope этого пайплайна.

## Карта объектов → скиллы

| Объект | Производящий скилл (P-номер) |
|---|---|
| `source_documents_inventory` | ingest stage (часть `ru-md-report-builder` P6) |
| `reliability_assessment` | `ru-financial-audit-rsbu` (P5) + `ru-mgmt-vs-rsbu-recon` (P2.5) |
| `revenue_profile` | `ru-revenue-by-direction` (P1.5) |
| `operating_economics` | `ru-cost-allocation-audit` (P1.5) |
| `tax_normalization` | `ru-whitening-math` (P0) + `ru-tax-risk-scan` (P1) |
| `client_base_assessment` (с `customers[]`) | `ru-client-base-quality` (P1.8) |
| `assets_inventory` | `ru-asset-inventory` (P2.8) |
| `owner_dependency` | `ru-owner-dependency-model` (P2.7) |
| `founder_exit_scenario` | расширение `ru-owner-dependency-model` (P2.7) |
| `valuation_basis` | `ru-valuation-basis-extract` (P1.7) |
| `seller_feedback_draft` | `ru-seller-feedback-draft` (P6.5) — использует [SELLER_FOLLOWUP_CATALOG.md](SELLER_FOLLOWUP_CATALOG.md) |
| `seller_deliverable_pack` | `ru-seller-deliverable-pack` (P6.7) — MD→PDF outbound |
| `escalation_recommendation` | `ru-escalation-router` (P7) |
| `open_questions` | агрегатор из всех скиллов, собирается в P6 |
| `TargetFinancialAssessment` | финальный wrap-up в `ru-md-report-builder` (P6) |

## Object specifications

### Общие конвенции

- Все денежные поля — в **рублях, integer**, без форматирования (`87500000`, не `87,5 млн ₽`).
- Все доли — **float [0..1]** (`0.62`, не `62%`).
- Все enum-поля имеют строго ограниченный набор значений; LLM не должен генерировать значения вне списка.
- Поле `confidence` (где применимо) — enum `low / medium / high`.
- Поле `evidence_basis[]` (где применимо) — список ссылок на исходные документы (имя файла после анонимизации + locator: страница / лист / диапазон ячеек).
- Любое неизвестное значение — `null`, **не** угадывать.

### 1. `source_documents_inventory`

```yaml
documents:
  - name: <anonymized filename>
    type: rsbu_form_1 | rsbu_form_2 | rsbu_form_4 | mgmt_pnl | finmodel_excel
         | client_list | contract | org_chart | bank_statement | seller_narrative | other
    period_from: YYYY-MM
    period_to: YYYY-MM
    entity: <entity pseudonym, e.g. TARGET-A>
    completeness: complete | partial | unreadable
missing_core_artifacts: []        # типы документов, которых не хватает для базового анализа
inventory_confidence: low | medium | high
```

### 2. `reliability_assessment`

```yaml
overall_reliability: low | medium | high
consistency_issues:
  - issue_type: arithmetic_mismatch | totals_unreconciled | conflicting_figures
              | unsupported_payback_claim | incompatible_metric_definitions
              | partially_missing_periods
    description: <one-liner>
    severity: low | medium | high
    evidence_basis: [...]
unsupported_seller_claims: []     # утверждения продавца без подтверждения в документах
accounting_management_alignment: aligned | partially_aligned | unclear | conflicting
can_proceed_to_normalization: yes | no | limited
notes: <free-form, ≤ 500 chars>
```

### 3. `revenue_profile`

```yaml
total_revenue: <int RUB | null>
core_service_revenue: <int RUB | null>           # профильная outsourcing
non_core_service_revenue: <int RUB | null>
hardware_revenue: <int RUB | null>               # перепродажа / box moving
one_off_project_revenue: <int RUB | null>
recurring_revenue_signal: weak | medium | strong
revenue_quality_risk: low | medium | high        # риск что top-line вводит в заблуждение
period: YYYY                                     # год к которому относятся цифры
evidence_basis: [...]
confidence: low | medium | high
```

### 4. `operating_economics`

```yaml
cogs_or_service_delivery_cost: <int RUB | null>
payroll_cost: <int RUB | null>
contractor_load: <int RUB | null>                # ИП/самозанятые в составе расходов
owner_compensation: <int RUB | null>             # см. перекрытие с owner_dependency.owner_withdrawals
overhead_cost: <int RUB | null>
gross_margin_estimate: <float [0..1] | null>
operating_margin_estimate: <float [0..1] | null>
margin_quality_comments: <free-form, ≤ 500 chars>
period: YYYY
evidence_basis: [...]
confidence: low | medium | high
```

### 5. `tax_normalization`

```yaml
optimization_signals:
  - signal_type: ip_workers_one_client | related_party_ip | usn_threshold_proximity
               | salary_cash_envelope | dropshipping_chain | other
    description: <one-liner>
    evidence_basis: [...]
likely_profit_distortion: none | low | medium | high
reported_net_profit: <int RUB | null>
normalized_net_profit_estimate: <int RUB | null>
whitening_gap_rub: <int RUB | null>              # reported − normalized (см. P0)
whitening_gap_share: <float [0..1] | null>
normalization_method_notes: <free-form, ≤ 800 chars>
required_follow_up_for_tax_clarity: []           # вопросы продавцу для уточнения
confidence: low | medium | high
```

### 6. `client_base_assessment`

```yaml
customer_count: <int | null>
top_1_share: <float [0..1] | null>
top_3_share: <float [0..1] | null>
top_5_share: <float [0..1] | null>
avg_revenue_per_customer: <int RUB | null>
contract_visibility: low | medium | high         # насколько мы видим договоры/сроки
avg_contract_duration_months: <int | null>
service_mix_known: yes | partial | no
transferability_risk: low | medium | high        # риск потери клиентов при смене собственника
change_of_control_clauses_detected: yes | partial | no | unknown
client_base_validity: weak | medium | strong
customers:                                       # per-client detail (заполняется при наличии раскладки)
  - pseudonym: <string, согласован с anonymizer mapping>
    services:                                    # услуги по этому клиенту
      - service_type: pto_abonentka | one_off_project | 1c_its | 1c_fresh
                    | hardware_resale | rent_compute | other
        monthly_fee_rub: <int | null>
        description: <free-form, ≤ 200 chars>
    total_monthly_revenue_rub: <int | null>
    contract_start_date: <YYYY-MM | null>
    current_contract_end_date: <YYYY-MM | null>
    historical_revenue_total_rub: <int | null>   # с даты начала по now
    calculated_ltv_rub: <int | null>             # если есть данные для расчёта
    transferability_per_client: low | medium | high | unknown
    notes: <free-form, ≤ 300 chars>
ltv_calculation_method: avg_contract_value | historical_actual | discounted_cashflow | null
evidence_basis: [...]
confidence: low | medium | high
```

> **Связь с анонимайзером:** `customers[].pseudonym` должен соответствовать псевдонимам в `mapping.json` сделки. Это позволяет связывать клиентскую раскладку с упоминаниями клиентов в других документах (договоры, ОСВ).

### 6a. `assets_inventory`

Что физически и юридически переходит в сделку. Критично для IT-аутсорса: оборудование и лицензии часто оформлены на ИП собственника или физлицо.

```yaml
hardware:
  - item_type: server | workstation | network | client_premises_equipment | other
    description: <free-form, ≤ 200 chars>
    quantity: <int>
    book_value_rub: <int | null>
    on_balance_of: target_entity | owner_ip | owner_personal | third_party | unknown
    physical_location: office | client_site | warehouse | with_employee | unknown
    transfer_status: transfers | requires_renegotiation | stays_with_seller | unknown
software_licenses:
  - license_type: 1c | microsoft | antivirus | itsm | monitoring | specialized | other
    description: <free-form, ≤ 200 chars>
    quantity: <int | null>
    annual_cost_rub: <int | null>
    registered_to: target_entity | owner_ip | owner_personal | client | unknown
    transfer_status: transfers | requires_renegotiation | stays_with_seller | unknown
ip:                                              # intellectual property
  - asset_type: methodology | runbook | internal_software | knowledge_base
              | automation_scripts | other
    description: <free-form, ≤ 300 chars>
    rights_held_by: target_entity | owner_personal | employee | shared | unclear
    transfer_status: transfers | requires_renegotiation | stays_with_seller | unknown
brand:
  - asset_type: domain | website | social_account | catalog_listing | trademark | other
    identifier: <string, e.g. domain name>
    registered_to: target_entity | owner_ip | owner_personal | unknown
    transfer_status: transfers | requires_renegotiation | stays_with_seller | unknown
client_base_as_asset:                            # клиентская база как отдельный актив
  formal_contracts_signed_with: target_entity | mix_target_and_owner_ip | owner_ip | mixed_unclear
  change_of_control_protection: present_in_majority | present_partial | absent | unknown
  estimated_transferable_share: <float [0..1] | null>
key_people:                                      # ключевые сотрудники как удерживаемый актив
  - role: <string>
    pseudonym: <string>
    criticality: low | medium | high
    retention_risk: low | medium | high | unknown
    formal_employment: trudovoy | ip | self_employed | informal | unknown
overall_transferable_asset_value_rub: <int | null>    # грубая оценка того, что реально переходит
assets_at_risk:                                  # активы под вопросом — самый важный output блока
  - item: <ссылка на конкретную запись выше>
    risk: <что именно может не перейти и почему>
    mitigation_needed: <что нужно сделать в SPA, чтобы перешло>
evidence_basis: [...]
confidence: low | medium | high
```

> **Главный смысл объекта:** не «опись имущества», а **разделение на 3 ведра**: что переходит автоматически, что требует отдельных переговоров (перерегистрация лицензий, переподписание договоров), что остаётся у продавца. Без этого post-deal экономика будет неверной.

### 7. `owner_dependency`

```yaml
owner_withdrawals: <int RUB | null>              # сколько собственник забирает
owner_operational_functions:                     # что собственник реально делает
  - function: delivery_lead | sales_lead | account_manager | tech_escalation
            | executive_glue | finance_ops | hr | client_relationship | other
    evidence_basis: [...]
owner_dependency_level: low | medium | high
estimated_replacement_roles:                     # кого надо нанять вместо собственника
  - role_title: <string>
    market_salary_rub_monthly: <int | null>
estimated_replacement_cost_annual: <int RUB | null>
post_owner_exit_profit_impact_rub: <int RUB | null>   # отрицательное = ухудшение
questions_for_next_meeting:                      # что нельзя понять из документов
  - <string>
confidence: low | medium | high
```

### 8. `founder_exit_scenario`

```yaml
stability_without_founders: stable | strained | materially_weaker | potentially_nonviable
lost_functions: []                               # что отвалится
required_replacements: []                        # что нужно компенсировать
estimated_added_cost_annual: <int RUB | null>
estimated_margin_change: <float | null>          # дельта operating margin
scenario_confidence: low | medium | high
evidence_basis: [...]
notes: <free-form, ≤ 600 chars>
```

### 9. `valuation_basis`

```yaml
asking_price: <int RUB | null>
seller_claimed_payback_years: <float | null>
seller_claimed_basis_type: ebitda | net_profit | revenue | undefined_narrative
extracted_ebitda: <int RUB | null>               # как у продавца
extracted_net_profit: <int RUB | null>           # как у продавца
normalized_ebitda: <int RUB | null>              # после whitening + tax normalization
normalized_net_profit: <int RUB | null>
implied_seller_multiple: <float | null>          # asking_price / extracted_ebitda
implied_normalized_multiple: <float | null>      # asking_price / normalized_ebitda
valuation_basis_comments: <free-form, ≤ 800 chars>
negotiation_readiness: weak | medium | strong    # хватает ли данных для торга
confidence: low | medium | high
```

### 10. `seller_feedback_draft`

```yaml
reviewed_materials_summary: <free-form, ≤ 600 chars>
preliminary_findings:
  - finding: <string>
    evidence_basis: [...]
unresolved_points:
  - point: <string>
    blocks_conclusion: <which conclusion we cannot reach without this>
requested_followups:
  - catalog_id: <ID из SELLER_FOLLOWUP_CATALOG.md | null если ad-hoc>
    artifact: <string — если catalog_id указан, берётся title из каталога>
    rationale: <why exactly — какой вывод без него невозможен>
    blocks_conclusion_ref: <ссылка на preliminary_findings[] или unresolved_points[]>
    not_a_general_request: true                  # маркер «обоснованный, не «пришлите ещё всё»»
tone: professional | exploratory | negotiating
```

> **Антипаттерн, который этот объект ловит:** «спасибо за 3 документа, пришлите ещё 4». Каждый `requested_followups[].rationale` должен указывать на конкретный `preliminary_findings` или `unresolved_points` через `blocks_conclusion_ref`.
>
> **Catalog lookup:** перед генерацией ad-hoc формулировки LLM ищет в [SELLER_FOLLOWUP_CATALOG.md](SELLER_FOLLOWUP_CATALOG.md) подходящий запрос по `unblocks_skill` / `confirms`. Ad-hoc формулировка допустима только если в каталоге ничего нет. Если ad-hoc формулировка повторяется на 3+ сделках — она кодифицируется как новая запись каталога.

### 10a. `seller_deliverable_pack`

Outbound артефакт для **отправки продавцу**: «Executive feedback pack». Цель — продемонстрировать экспертизу, серьёзность намерений и дать содержательную обратную связь, а не просто запросить новые документы. Финальный формат — PDF (MD → pandoc).

```yaml
title: <string, e.g. "Предварительная оценка бизнеса TARGET-A">
prepared_for: <string, e.g. "Иван Иванов, собственник">
prepared_at: <ISO date>
sections:
  business_understanding:                        # «как мы поняли ваш бизнес»
    summary: <free-form, ≤ 1500 chars>
    revenue_structure_observed: <≤ 800 chars>
    operating_model_observed: <≤ 800 chars>
    based_on_documents: [...]                    # ссылки на присланные документы
  strengths:                                     # что увидели как силу бизнеса
    - point: <string>
      evidence: <string>
  areas_of_concern:                              # что увидели как слабости/риски (мягкие формулировки)
    - point: <string>
      evidence: <string>
      reframe_as_question: <string>              # переведено в вопрос, не в обвинение
  preliminary_valuation_range:
    basis: ebitda_multiple | net_profit_multiple | payback | revenue_multiple | not_disclosed
    range_low_rub: <int | null>
    range_high_rub: <int | null>
    range_disclosed_to_seller: yes | no | with_caveats
    caveats: <≤ 600 chars>                       # «оценка предварительная, зависит от уточнений»
  next_steps_for_seller:                         # что нужно для уточнения оценки
    - title: <string>
      from_catalog_id: <ID из SELLER_FOLLOWUP_CATALOG.md | null>
      why_we_need_it: <≤ 300 chars, человеческая формулировка>
  closing_note: <free-form, ≤ 500 chars>
tone: professional | warm_professional | exploratory
output_format: pdf | md_only | both
disclosed_uncertainties: <bool>                  # сообщаем ли продавцу о слабых местах данных
internal_only_appendix:                          # секция, которая в PDF не попадает
  things_we_noticed_but_did_not_disclose: []     # держим у себя как переговорные карты
```

> **Принципиальные ограничения этого артефакта:**
> - Не сообщаем продавцу всё, что заметили — `internal_only_appendix` остаётся у нас как переговорные карты.
> - `preliminary_valuation_range` может быть `range_disclosed_to_seller: no` — на ранней стадии часто лучше не называть цифры.
> - `areas_of_concern[].reframe_as_question` обязателен: «выручка от связанных лиц» становится «как вы видите долгосрочную устойчивость выручки от группы компаний, аффилированных с вашим ИП?».
> - Формат PDF — стандартизированный шаблон pandoc, не «дизайнерская презентация». Сила в содержании, не в графике.

### 11. `escalation_recommendation`

```yaml
recommendation: stay_automated | send_to_internal_analyst | send_to_external_expert
reason_codes:
  - low_data_reliability_high_strategic_interest
  - material_tax_normalization_ambiguity
  - high_owner_dependency_uncertainty
  - significant_price_vs_normalized_economics_mismatch
  - client_base_transferability_uncertain_undocumentable
  - other
priority_level: low | medium | high
expected_value_of_human_review: <int RUB | null>     # грубая оценка outcome дельты
tier_cost_estimate_rub: <int RUB | null>             # 0 / время аналитика / ~40-45k для tier 3
notes: <free-form>
```

### 12. `open_questions`

```yaml
- question: <string>
  category: tax | owner_role | client_base | revenue_structure | legal | operational | other
  required_for: <какой объект/вывод нельзя завершить без ответа>
  best_source: documents | seller_call | external_data | analyst_review
```

Агрегируется из всех скиллов, дедуплицируется, передаётся в `seller_feedback_draft.requested_followups`.

### 13. `TargetFinancialAssessment` (root object)

```yaml
target_slug: <string>
assessed_at: <ISO date>
assessment_version: <semver>
source_documents_inventory: <object §1>
reliability_assessment: <object §2>
revenue_profile: <object §3>
operating_economics: <object §4>
tax_normalization: <object §5>
client_base_assessment: <object §6>
assets_inventory: <object §6a>
owner_dependency: <object §7>
founder_exit_scenario: <object §8>
valuation_basis: <object §9>
seller_feedback_draft: <object §10>
seller_deliverable_pack: <object §10a>          # outbound PDF, не часть internal report
escalation_recommendation: <object §11>
open_questions: <list of §12>
```

Это **единственный** объект, который покидает пайплайн. `seller_deliverable_pack` рендерится из него в PDF и уходит наружу — но сам root остаётся внутренним.

## Pipeline flow

```
ingest
  └─ source_documents_inventory
        │
        ▼
reliability layer
  └─ reliability_assessment          ← gate: can_proceed_to_normalization?
        │
        ▼ (если yes / limited)
normalization layer (parallel)
  ├─ revenue_profile
  ├─ operating_economics
  └─ tax_normalization               ← whitening_gap считается здесь
        │
        ▼
asset-quality layer (parallel)
  ├─ client_base_assessment          ← + customers[] с per-client LTV
  ├─ assets_inventory                ← hardware/licenses/IP/brand/key_people + transfer_status
  └─ owner_dependency
        │
        ▼
scenario layer
  └─ founder_exit_scenario           ← зависит от owner_dependency
        │
        ▼
valuation prep
  └─ valuation_basis                 ← опирается на normalized_* из tax_normalization
        │
        ▼
output layer
  ├─ open_questions (агрегатор)
  ├─ seller_feedback_draft           ← lookup в SELLER_FOLLOWUP_CATALOG.md
  └─ escalation_recommendation       ← опирается на reliability + whitening_gap + dependency
        │
        ▼
internal report (root)
  └─ TargetFinancialAssessment
        │
        ▼
outbound (опционально)
  └─ seller_deliverable_pack         ← rendered MD→PDF, отправляется продавцу
```

Gate в reliability layer — критический: если `can_proceed_to_normalization: no`, дальнейшие слои **не запускаются**, пайплайн сразу идёт в `seller_feedback_draft` с запросом базовых артефактов и в `escalation_recommendation` с пометкой «недостаточно данных».

## Что меняется в `PORTRAIT.md` (RU_ADAPTATION_PLAN.md, P6)

`PORTRAIT.md` сделки = сериализация `TargetFinancialAssessment` в YAML-frontmatter + ссылки на 01-08 секции. Поля frontmatter из существующего плана (`revenue_2025`, `ebitda_reported`, `ebitda_whitened`, `tax_risk_total_rub`, `recommendation`) — это подмножество этой схемы. Их надо привести в соответствие:

| Текущее поле в PORTRAIT.md | Поле в схеме |
|---|---|
| `revenue_2025` | `revenue_profile.total_revenue` |
| `ebitda_reported` | `valuation_basis.extracted_ebitda` |
| `ebitda_whitened` | `valuation_basis.normalized_ebitda` |
| `tax_risk_total_rub` | `tax_normalization.whitening_gap_rub` |
| `recommendation` | `escalation_recommendation.recommendation` |

Это нужно отразить в `ru-md-report-builder` (P6) при имплементации.
