---
name: ru-financial-audit-rsbu
description: Audit financial documents under RSBU (forms 1/2/4) — cross-check between forms, sanity-check against management accounts, detect typical anomalies (sudden "other expenses", related-party transactions, debiторка > 180 days, kreditorka aging concentration, hidden obligations), seasonality of revenue. Embeds AVE+Fomichev practice: working capital deep-dive (debiторка, kreditorka, tax debts, management↔RSBU reconciliation). Replaces upstream US-GAAP audit assumptions. Triggers on "RSBU audit", "финансовый аудит", "формы 1 2 4", "working capital", "дебиторка", "кредиторка", "сходимость управ vs бух", "аномалии".
---

# RSBU Financial Audit (P5)

Апстрим спрашивает QoE и Big-4 audit history — у МСБ это не работает. Здесь — РСБУ-аудит: кросс-сверка форм, сопоставление с управленческим, working capital deep-dive (практика АВЕ+Фомичева), типовые аномалии.

**Reliability check** (слой 1 из 10 смысловых слоёв в брифе) реализуется этим скиллом + P2.5 `ru-mgmt-vs-rsbu-recon`.

## When to use

- В пакете есть РСБУ-отчётность (формы 1, 2, желательно 4) минимум за 3 года
- Завершён P0.5 (multi-entity recon) — аудит делается по всем entities группы
- Параллельно с P1.5 (cost allocation) и P2.5 (mgmt vs RSBU)

## Inputs

- Бухотчётность РСБУ формы 1 / 2 / 4 за 3 года по всем entities группы
- Управленческий ОПиУ за тот же период (для cross-check)
- ОСВ по контрагентам (для working capital deep-dive)
- Налоговые декларации (УСН/ОСНО) за 3 года — для cross-check «начислено vs уплачено»

## Workflow

### Step 1: Cross-check форм 1/2/4

Стандартные тождества РСБУ:
- Σ статей актива баланса = Σ статей пассива
- Чистая прибыль (форма 2) → нераспределённая прибыль (форма 1) через ΔKapital
- ДДС (форма 4): Δ денежных средств в форме 1 = NetCF в форме 4

Расхождения — флаги:
- Несостыковки в копейках — округление, ок
- Несостыковки >1% — ошибка отчётности или скрытые операции

### Step 2: Сопоставление с управленческим (вход в P2.5)

| Метрика | Форма 2 (РСБУ) | Управ.ОПиУ | Δ | Допустимо? |
|---|---|---|---|---|
| Выручка | … | … | … | Δ ≤5% — ок (разница в признании); >10% — флаг |
| ФОТ + страховые | … | … | … | Должны почти совпадать |
| Прочие расходы | … | … | … | Часто скрытое |
| Чистая прибыль | … | … | … | Большое Δ — скрытые потоки |

Передаётся в P2.5 для детального разбора расхождений.

### Step 3: Working capital sub-audit (практика АВЕ+Фомичева)

#### 3.1. Кредиторская задолженность

```yaml
kreditorka_audit:
  total_rub: 18500000
  aging:
    up_to_90_days_rub: 12000000
    90_to_180_days_rub: 4200000
    180_to_365_days_rub: 1800000
    over_365_days_rub: 500000           # высокий риск — почему висит?
  top_5_share_pct: 67                   # концентрация
  related_party_share_pct: 24           # доля связанных сторон → флаг
  loans_from_founders_rub: 3000000      # отдельная строка
  hidden_obligations_signals:
    - "договор с CLIENT-007 на 4M ₽ не отражён в формах"
```

#### 3.2. Дебиторская задолженность

```yaml
debiторka_audit:
  total_rub: 12000000
  aging:
    up_to_90_days_rub: 8500000
    90_to_180_days_rub: 2200000
    180_to_365_days_rub: 1000000
    over_365_days_rub: 300000           # скорее всего безнадёжная
  bad_debt_reserve_rub: 0                # ожидание ≥300k → флаг недосозданного резерва
  top_5_client_share_pct: 78
  intra_group_share_pct: 18              # внутригрупповая (из P0.5)
  collectability_assessment: medium
```

#### 3.3. Налоговые задолженности

```yaml
tax_debt_audit:
  public_debt_from_rusprofile_rub: 0
  restructured_signals: false
  uplatcheno_vs_nachisleno:               # по ДДС vs декларациям
    profit_tax_gap_rub: 0
    vat_gap_rub: -150000                  # отрицательный = недоплачено? проверить
    insurance_gap_rub: 0
  pending_disputes: []
  active_audits: []
```

#### 3.4. Сходимость управ ↔ бух (передача в P2.5)

Не повторять детально — здесь только high-level флаг «расхождения есть/нет, severity», полный разбор в P2.5.

### Step 4: Типовые аномалии

| Аномалия | Как проверить | Severity |
|---|---|---|
| Резкий рост «прочих расходов» | YoY изменение строки 2350 формы 2 >50% | medium |
| Сезонность выручки сильнее ожидаемой | Помесячный coefficient of variation >0.3 | medium (для аутсорса) |
| Аффилированные сделки в крупных суммах | Из ОСВ по контрагентам, сравнить с списком аффилированных (P0.5) | high |
| Дебиторка >180 дней растёт | YoY изменение | medium |
| Запасы (для услуг должны быть 0) | Строка 1210 баланса >0 для чистого аутсорса | medium |
| Отрицательный operating CF при положительной прибыли | Forma 4 vs Forma 2 | high (косвенно — «бумажная» прибыль) |

### Step 5: Reliability verdict

Итоговый verdict качества входных данных:

```yaml
reliability:
  forms_internal_consistency: pass
  forms_vs_mgmt_alignment_pct: 87
  working_capital_quality: medium
  anomalies_count: 4
  anomalies_severity_max: high
  overall: medium                       # high | medium | low
  confidence_for_downstream_skills: medium
  blockers: []
```

Этот verdict — **gate в pipeline**: если `overall: low`, P0 whitening запускается с `confidence: low` и автоматически рекомендует Tier 2 review.

### Step 6: Output

**MD-секция `## Financial audit (RSBU)`** + frontmatter `financial_audit_rsbu` с reliability verdict + working_capital_audit + anomalies[].

## Output contract

См. [PIPELINE_SCHEMA.md](../../../../../PIPELINE_SCHEMA.md), объект `FinancialAuditRSBU`. **Consumers:** P0 (confidence gate), P1 (working capital для tax-risk: hidden cash signal), P2.5 (детальный разбор расхождений), P7 (reliability=low → mandatory Tier 2).

## Failure modes & guardrails

- **Не путать с независимым аудитом.** Это не заключение, а **методичный cross-check** по фиксированным правилам.
- **РСБУ ≠ управ ≠ ОСНО налоговая.** Три разных набора цифр. Cross-check фокусируется на расхождениях, а не на «правильности».
- **«Прочие расходы» в форме 2** — часто помойка. Помечать как `requires_drilldown`, переключать на ОСВ по 91 счёту.
- **Если нет ОСВ** — working capital aging невозможен. `confidence: low` для этого блока, явный запрос в P6.5.
- **Если 2 entities, формы только по одной** — partial reliability, флаг для P0.5.

## Связанные скиллы

- **Prerequisites:** P0.5 (карта entities)
- **Параллельно:** P1.5 (cost allocation), P2.5 (mgmt vs RSBU)
- **Downstream:** P0 (confidence gate), P1 (tax signals), P7 (escalation gate)
