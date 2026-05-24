---
name: ru-escalation-router
description: Routing decision at the end of the pipeline — Tier 1 (LLM-only sufficient) / Tier 2 (internal analyst review needed) / Tier 3 (external expert engagement required ~40-45k RUB). Decision based on reliability verdict (P5), whitening_gap size (P0), client base validity (P1.8), 152-FZ/KII blockers (P3), owner-dependency scenario D probability (P2.7), and deal stage. Produces a single recommendation with reasoning. Triggers on "escalation", "routing", "tier 1 2 3", "нужен ли аналитик", "external review".
---

# Escalation Router (P7)

Финальный шаг пайплайна. Решение, можно ли двигаться дальше на основе LLM-вывода (Tier 1), нужен ли внутренний аналитик по фиксированной таблице (Tier 2), или нужен внешний эксперт ~40-45k ₽ (Tier 3).

Это **не оценка качества пайплайна**, это **routing по риску ошибки и стадии сделки**.

## When to use

- Завершён P6 (PORTRAIT.md собран) — все frontmatter доступны
- Перед принятием любого решения о следующем шаге сделки (LOI, отказ, продолжение DD)

## Inputs (читает из PORTRAIT.md frontmatter)

- `reliability.overall` (P5)
- `whitening.whitening_gap_pct` (P0)
- `tax_risk_scan.total_impact_base_rub` (P1)
- `client_base_assessment.coc_exposure.total_revenue_at_coc_risk_pct` (P1.8)
- `compliance_152fz_kii.kii_blocker` (P3)
- `owner_dependency.scenarios.D.probability` (P2.7)
- `valuation_basis.whitened_recompute.scenario_A.gap_to_asking_pct` (P1.7)
- `it_accreditation.sustainability_verdict` (P2)
- Deal stage: screening / pre-LOI / post-LOI / pre-closing

## Workflow

### Step 1: Tier 1 (LLM достаточно) — критерии

ВСЕ должны выполняться:
- `reliability.overall: high`
- `whitening.whitening_gap_pct < 30`
- `tax_risk.total_impact_base_rub < 10000000` (10M ₽)
- `client_base_assessment.coc_exposure.total_revenue_at_coc_risk_pct < 25`
- `compliance_152fz_kii.kii_blocker: false`
- `owner_dependency.scenarios.D.probability < 0.15`
- Deal stage: screening (на этой стадии Tier 1 окончательное решение)

**Действие на Tier 1:**
- Если decision = `proceed_to_pre_loi` → продолжаем с Tier 1 материалами
- Если decision = `walk_away` → отказ без эскалации
- Если decision = `request_more_info` → P6.5 followup, re-run

### Step 2: Tier 2 (внутренний аналитик) — критерии

Любое из (ИЛИ Tier 1 не прошёл, но не сработали Tier 3 триггеры):
- `reliability.overall: medium`
- `30 ≤ whitening_gap_pct < 60`
- `10M ≤ tax_risk_base < 30M`
- `25 ≤ coc_risk_pct < 50`
- `0.15 ≤ owner_dependency_D_prob < 0.30`
- `it_accreditation.sustainability_verdict: at_risk`
- Deal stage: pre-LOI или дальше

**Действие на Tier 2:**
- Передать PORTRAIT.md + 8 секций внутреннему аналитику
- Аналитик работает по той же стандартной форме — заполняет / корректирует frontmatter
- Output: те же поля + `tier_2_review:` блок с annotations и corrections
- Бюджет: дни сотрудника, без external cost

### Step 3: Tier 3 (внешний эксперт, ~40-45k ₽) — критерии

Любое из (mandatory escalation):
- `reliability.overall: low`
- `whitening_gap_pct ≥ 60`
- `tax_risk.total_impact_high_rub ≥ 30000000` (high estimate, не base!)
- `coc_risk_pct ≥ 50`
- `compliance_152fz_kii.kii_blocker: true` (КИИ-блокер всегда Tier 3)
- `owner_dependency.scenarios.D.probability ≥ 0.30`
- `spa.indemnity_cap_rub > deal_price × 0.5` (требует juриста)
- Deal stage: pre-closing (последний rung перед deal)
- ИЛИ: совокупность 3+ Tier 2 триггеров

**Действие на Tier 3:**
- Внешний подрядчик: налоговый аудитор (если tax-risk доминирует) ИЛИ юрист (если SPA / КИИ) ИЛИ оба
- Бюджет: 40-45k ₽ за одну проверку, до 40k ₽ начиная с 3-й (см. экономика tiered analysis в плане)
- Output: внешнее заключение → human merge в PORTRAIT.md

### Step 4: Decision matrix (сводно)

```yaml
escalation_decision:
  tier: 2
  reasoning:
    - "reliability.overall = medium → not Tier 1"
    - "whitening_gap_pct = 48 → Tier 2 range"
    - "tax_risk_base = 14.8M → Tier 2 range"
    - "deal_stage = pre_loi → review before LOI"
    - "no Tier 3 mandatory triggers"
  action: "internal_analyst_review_before_loi"
  estimated_horizon_days: 5
  estimated_cost_rub: 0   # внутренние часы
  next_review_after: "получение answers к followup v3 ИЛИ analyst_annotation"
  blockers_to_clear_for_tier_downgrade: ["confidence on whitening structure (нужны данные по структуре занятости)"]
```

### Step 5: Special cases

- **Если decision = `walk_away`:** routing → no escalation, archive deal с reasoning
- **Если decision = `proceed_to_closing` после Tier 2/3:** required artifact = `tier_2_review` или `tier_3_review` блок в PORTRAIT.md (без него — refuse to release)
- **Если несколько Tier 3 триггеров одновременно:** разбить на отдельные external reviews (налоговый + юрист отдельно)
- **Если portfolio chronicle accumulated** (Addendum 4b, post-pilot) — учитывать historical benchmarks: «у 4 из 7 кейсов с whitening_gap 40-60% Tier 2 был достаточен»

### Step 6: Output

**Frontmatter в PORTRAIT.md:**

```yaml
recommendation:
  tier: 2
  action: internal_analyst_review_before_loi
  reasoning_lines: ["...", "..."]
  blockers: ["..."]
  estimated_horizon_days: 5
  estimated_cost_rub: 0
  next_review_trigger: "..."
  decision_date: 2026-05-24
  decision_version: v3
```

**MD-секция в `01-summary.md`:**

```markdown
## Recommendation

**Tier 2** — internal analyst review before LOI.

**Reasoning:**
- Reliability medium (формы 1/2 ок, mgmt vs RSBU есть расхождения 12%)
- Whitening gap 48% — в Tier 2 range
- Tax risk base 14.8M — significant, но не >30M high
- No КИИ blocker, no Tier 3 mandatory triggers

**Action:** Передать PORTRAIT.md + 8 секций аналитику. Особое внимание: working capital + cost allocation + структура занятости.
```

## Output contract

См. [PIPELINE_SCHEMA.md](../../../../../PIPELINE_SCHEMA.md), объект `EscalationDecision`. **Final producer** в пайплайне (после P6, перед external action). Consumer: человек, принимающий решение по сделке + (optionally) auto-trigger Tier 2 workflow.

## Failure modes & guardrails

- **Tier 1 не означает «high confidence».** Это «hodder для screening, можно решать самостоятельно». На pre-closing Tier 1 невалиден.
- **Tier 3 = mandatory** при определённых триггерах (КИИ, high tax-risk, indemnity > 50% price). Не downgrade-able.
- **Не пытаться угадать стоимость Tier 3.** 40-45k — это исторический бенчмарк, актуальные цены — input оператора.
- **Decision_version инкрементируется при каждом re-run.** Старые decisions не удаляются.
- **Blockers_to_clear_for_tier_downgrade** — критическое поле. Чёткий ответ: что должно случиться, чтобы Tier 2 → Tier 1.

## Связанные скиллы

- **Reads from:** ВСЕ P0-P6 (через PORTRAIT.md frontmatter)
- **Triggers:** P6.5 (если decision = request_more_info), Tier 2 workflow (внешний), Tier 3 procurement (внешний)
- **Coupled with:** [ADDENDUM_FROM_DD_AGENTS.md](../../../../../ADDENDUM_FROM_DD_AGENTS.md) §3 (Judge agent — quality gate, дополнительно после стабилизации) и §4 (portfolio chronicle — для бенчмарок)
