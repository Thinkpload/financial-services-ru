---
name: ru-asset-inventory
description: Inventory all assets the deal touches (hardware, software licenses, IP, brand, key people, client base as asset) and bucket each into one of three transfer states — transfers / requires_renegotiation / stays_with_seller. Critical for IT-outsourcing where licenses and equipment are often registered to the owner's personal IP or individual rather than to the target LLC. Without this, post-deal economics are wrong — buyer doesn't know what physically and legally transfers. Triggers on "asset inventory", "что переходит", "лицензии", "оборудование", "asset transfer", "stays with seller".
---

# Asset Inventory (P2.8)

В МСБ ИТ-аутсорсе типичная находка: «лицензия 1С на 50 рабочих мест оформлена на ИП собственника, оборудование (50% серверов) — на физлицо собственника, домен на бывшую жену». На бумаге у ЮЛ актива нет. После сделки — либо платим за переоформление, либо теряем актив.

Скилл строит полную картину: что переходит автоматически, что требует переговоров (с собственником / вендором), что **не переходит вообще** и должно быть выкуплено / переоформлено / заменено.

## When to use

- Параллельно с P0.5 (на каких entities активы оформлены)
- Перед SPA (P4) — структура assets transfer прописывается явно
- Перед формированием preliminary_valuation_range (некоторые активы покупаются отдельно от ЮЛ)

## Inputs

- Реестр оборудования с принадлежностью (на каком ЮЛ / ИП / физлице)
- Реестр лицензий ПО (1С, MS, Linux Pro, специализированный софт) — на ком оформлены
- Список товарных знаков, доменов, прав на код, методологий, базы знаний
- Договоры аренды офиса и оборудования
- Ключевые люди (из P2.7) — формально не assets но фактически да

## Workflow

### Step 1: Категории активов

Шесть стандартных категорий:

| Категория | Примеры | Типичные риски |
|---|---|---|
| `hardware` | серверы, ноутбуки, сетевое | оформлено на ИП/физлицо собственника |
| `software_licenses` | 1С, MS Volume, специализированный софт | partner-аккаунт у собственника, лицензии «прилипают» к нему |
| `ip` | внутренний код, методологии, базы знаний | права принадлежат физлицам без передачи |
| `brand` | товарный знак, домен, сайт, бренд-бук | домен на физлицо, ТЗ не зарегистрирован |
| `key_people` | топ-сотрудники | формально не актив, фактически основной |
| `client_base_as_asset` | контракты, recurring | change-of-control риски (P1.8) |

### Step 2: Inventory по каждому активу

Для каждого:

```yaml
- asset_id: hw-001
  category: hardware
  description: "Сервер Dell PowerEdge R740, основной production"
  registered_to_entity: "ИП-OWNER-1"
  bv_rub: 450000
  fair_value_rub: 600000
  transfer_status: requires_renegotiation
  transfer_terms_proposed: "выкуп по BV"
  risk_if_not_transferred: "production downtime, потеря 2 клиентов на SLA"
  notes: "критический"
```

### Step 3: Bucket assignment

Три ведра:

**`transfers` — переходит вместе с ЮЛ автоматически:**
- Активы на покупаемой entity
- Договоры без change-of-control
- Лицензии в волюм-программе на ЮЛ

**`requires_renegotiation` — переходит, но требует действий:**
- Активы на собственнике (ИП/физлицо) → нужен договор выкупа в SPA
- Лицензии партнёрской программы (нужно либо переоформление, либо новые)
- Договоры аренды с change-of-control оговоркой
- Domain на физлицо → договор о передаче

**`stays_with_seller` — НЕ переходит:**
- Активы, которые собственник явно оставляет себе
- Лицензии, не подлежащие переоформлению (например, персональные сертификации)
- Бренд, если собственник сохраняет родственный бизнес

### Step 4: Денежная оценка

```yaml
asset_transfer_costs:
  buyout_required_rub: 1850000           # выкуп hardware от ИП собственника
  license_renewal_required_rub: 720000    # новые волюмы 1С
  replacement_required_rub: 350000        # что не выкупается
  total_one_time_rub: 2920000
```

Эта сумма — **отдельная строка в pre-deal costs** для P6.7 (preliminary_valuation_range) и P4 (SPA — закладывается в structure deal price ИЛИ as side-purchase agreement).

### Step 5: Output

**MD-секция `## Asset inventory`:**

```markdown
## Asset inventory

### Сводка по bucket
| Bucket | Кол-во активов | BV ₽ | Fair value ₽ |
|---|---|---|---|
| Transfers | … | … | … |
| Requires renegotiation | … | … | … |
| Stays with seller | … | … | … |

### Критические активы (requires_renegotiation, high risk)
[таблица с описанием, статусом, предлагаемыми условиями]

### Денежная оценка переоформления
[блок из Step 4]

### SPA implications
- Side-purchase agreement: hardware от ИП собственника на 1.85M ₽
- License renewal pre-close: 1С волюмы 720k ₽
- Brand transfer (товарный знак): включить в SPA отдельным пунктом
```

**Frontmatter:**
```yaml
asset_inventory:
  total_assets_count: 47
  transfers_count: 28
  requires_renegotiation_count: 14
  stays_with_seller_count: 5
  one_time_transfer_cost_rub: 2920000
  critical_at_risk: ["hw-001 production server", "1c-lic-volume"]
  confidence: medium
```

## Output contract

См. [PIPELINE_SCHEMA.md](../../../../../PIPELINE_SCHEMA.md), объект `AssetInventoryAssessment`. **Consumers:** P4 (SPA structure — side-purchase / transfer clauses), P6.7 (valuation impact), P7 (high % stays_with_seller → Tier 2).

## Failure modes & guardrails

- **«На ком оформлено»** должно быть подтверждено документом (договором / накладной / лицензионным соглашением), не словами продавца.
- **Если данных нет** — `confidence: low` + явный запрос в P6.5 (catalog_id: asset_ownership_audit).
- **Не путать «принадлежит entity» и «использует entity».** Аренда — отдельный transfer_status (requires_renegotiation если есть CoC у арендодателя).
- **Brand/ТЗ:** если товарный знак не зарегистрирован — это сразу `stays_with_seller` де-факто (защиты нет, перейти нечему).

## Связанные скиллы

- **Prerequisites:** P0.5 (карта entities), P2.7 (key people как assets)
- **Downstream:** P4 (SPA structure), P6.7, P7
