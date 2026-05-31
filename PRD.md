# CanonIQ — Product Requirements Document

**CanonIQ: AI-Powered Canonical Mapping Engine**

> Map messy source data into trusted canonical models.

| | |
|---|---|
| **Document status** | Enhanced & consolidated PRD (supersedes the two source PDFs) |
| **MVP version** | v0.1.0 |
| **Last updated** | 2026-05-29 |
| **Owner** | CanonIQ maintainers |
| **License intent** | Apache-2.0 (permissive, enterprise-friendly) |

This document merges the original **CanonIQ PRD** and the **Multi-Source / Multi-Format PRD Update** into a single authoritative specification, and upgrades the canonical schemas to align with the data standards real companies use in production (HL7 FHIR, ISO 20022, GS1/GTIN, 1EdTech OneRoster, Ed-Fi, CEDS, HR Open Standards, and the ISO/RFC primitives that underpin them). Higher education is **one example domain only** — the engine is domain-agnostic and source-agnostic by design.

---

## Table of Contents

1. [Product Summary](#1-product-summary)
2. [Core Problem](#2-core-problem)
3. [Product Vision & Positioning](#3-product-vision--positioning)
4. [Goals, Non-Goals & Success Metrics](#4-goals-non-goals--success-metrics)
5. [Target Users & Jobs-to-be-Done](#5-target-users--jobs-to-be-done)
6. [Product Principles](#6-product-principles)
7. [System Architecture](#7-system-architecture)
8. [Core Data Models](#8-core-data-models)
9. [Canonical Schema Format (Production-Grade)](#9-canonical-schema-format-production-grade)
10. [Reference Canonical Schemas by Domain](#10-reference-canonical-schemas-by-domain)
11. [Type System & Inference](#11-type-system--inference)
12. [Pattern & PII Detection](#12-pattern--pii-detection)
13. [Matching Engine & Confidence Scoring](#13-matching-engine--confidence-scoring)
14. [Validation Rule Generation](#14-validation-rule-generation)
15. [Transformation](#15-transformation)
16. [Schema Drift Detection](#16-schema-drift-detection)
17. [Connectors: Multi-Source Architecture](#17-connectors-multi-source-architecture)
18. [Profilers: Source-Agnostic Profiling](#18-profilers-source-agnostic-profiling)
19. [Source Configuration & Secrets](#19-source-configuration--secrets)
20. [Output Artifacts (Contracts)](#20-output-artifacts-contracts)
21. [CLI Specification](#21-cli-specification)
22. [Python SDK Specification](#22-python-sdk-specification)
23. [Optional AI Adapter](#23-optional-ai-adapter)
24. [Non-Functional Requirements](#24-non-functional-requirements)
25. [Security & Privacy](#25-security--privacy)
26. [Technology Stack & Packaging](#26-technology-stack--packaging)
27. [Repository Structure](#27-repository-structure)
28. [Testing Strategy](#28-testing-strategy)
29. [Documentation Requirements](#29-documentation-requirements)
30. [Roadmap](#30-roadmap)
31. [Acceptance Criteria](#31-acceptance-criteria)
32. [Build Plan for Claude Code](#32-build-plan-for-claude-code)
33. [Glossary & Standards Reference](#33-glossary--standards-reference)

---

## 1. Product Summary

CanonIQ is an **open-source, local-first, domain-agnostic canonical schema mapping engine** for enterprise data onboarding, validation, transformation, and schema-drift detection.

CanonIQ converts inconsistent source data — from customers, vendors, partners, SaaS tools, databases, warehouses, data lakes, APIs, and internal systems — into standardized canonical models. It:

- **Profiles** source datasets (types, null rates, uniqueness, samples, patterns, PII signals).
- **Loads** user-defined, versioned canonical schemas.
- **Suggests** source→canonical field mappings with a transparent confidence score and human-readable reasons.
- **Scores & gates** mappings into `auto_approved`, `requires_review`, or `low_confidence`.
- **Generates** validation rules from the canonical schema + profile.
- **Transforms** source data into canonical output.
- **Detects** schema drift between ingestions.

CanonIQ separates **data access** (connectors) from **schema intelligence** (profilers + matchers). Connectors fetch or sample data; profilers understand structure; the mapping engine stays source-agnostic.

CanonIQ is usable as a **Python SDK** and a **CLI** today, with a future server/API mode, review-workflow UI, and managed service. It is privacy-conscious, extensible (domain packs + connector plugins), and open-source ready.

---

## 2. Core Problem

Companies ingest data describing the same entities under different names, types, formats, and conventions. Mapping these by hand is slow, error-prone, undocumented, and breaks silently when upstream schemas change.

**Examples across domains (source → canonical):**

```text
Higher education     banner_id          -> student_id
                     student_email      -> email
                     cumulative_gpa     -> gpa
                     last_activity_at   -> last_lms_login

Retail / e-commerce  sku_id             -> product_id (mapped to GTIN where present)
                     item_name          -> product_name
                     available_qty      -> inventory_quantity
                     sale_price         -> price (with price_currency)

Healthcare           patient_mrn        -> patient_id (FHIR Patient.identifier[MR])
                     dob                -> date_of_birth (FHIR Patient.birthDate)
                     diagnosis_code     -> condition_code (ICD-10-CM / SNOMED CT)
                     visit_time         -> encounter_period_start (FHIR Encounter)

Finance              acct_num           -> account_id (IBAN where applicable)
                     txn_amt            -> amount (+ amount_currency, ISO 4217)
                     txn_date           -> booking_datetime (ISO 8601)
                     cust_email         -> customer_email

Logistics            shipment_no        -> shipment_id (SSCC where applicable)
                     tracking_num       -> tracking_number
                     origin_zip         -> origin_postal_code
                     delivery_eta       -> estimated_delivery_at (ISO 8601)
```

**The core question:** How do we automatically profile inconsistent source schemas, suggest mappings to canonical models, explain those mappings, validate values, transform data, and detect drift over time — without lock-in to a single domain or data source?

---

## 3. Product Vision & Positioning

> **CanonIQ becomes the standard open-source toolkit for canonical schema mapping, data onboarding, AI-ready data preparation, and schema-drift detection — source-agnostic and domain-agnostic.**

It answers, for any incoming dataset:

1. What fields exist?
2. What do they likely mean?
3. Which canonical fields do they map to?
4. How confident are we, and why?
5. What validation rules should protect this data?
6. What changed since the last ingestion?
7. Is the data ready for analytics, AI agents, ML, or business workflows?

**Positioning statement:** *A universal canonical mapping engine that profiles and maps data from files, data lakes, databases, warehouses, SaaS platforms, and APIs into trusted canonical models.* CanonIQ is not tied to one domain or one data source.

---

## 4. Goals, Non-Goals & Success Metrics

### 4.1 Goals

CanonIQ should: profile source datasets; load versioned canonical schemas; suggest mappings; score confidence; explain every suggestion; generate validation rules; transform to canonical output; detect drift; support multiple domains; support CLI + SDK; be local-first; be open-source ready; be extensible via domain packs and connector plugins; support **optional** AI-assisted mapping without requiring external AI.

### 4.2 Non-Goals (MVP)

- Full production web UI; hosted SaaS; complex auth/RBAC.
- Mandatory external LLM calls; real-time streaming ingestion.
- Full Spark support; full enterprise data-catalog integration.
- Fully implemented database/cloud connectors (placeholders only in MVP).
- Complex derived-field transformations; multi-user approval workflows.

### 4.3 Success Metrics (measurable acceptance signals)

| Metric | Target (MVP) |
|---|---|
| Mapping precision on labeled fixtures (auto_approved correct) | ≥ 0.95 |
| Mapping recall on labeled fixtures (true mappings surfaced ≥ requires_review) | ≥ 0.90 |
| Profiling throughput (local CSV) | ≥ 100k rows / sampling window in < 5s |
| Cold install footprint (`pip install canoniq`, core only) | No cloud/db deps pulled |
| Test coverage | ≥ 80% line coverage; all 5 domains exercised |
| Zero external network calls during `pytest` | Enforced in CI |

*Confidence thresholds and weights are configurable; the targets above are validated against the bundled synthetic fixtures.*

---

## 5. Target Users & Jobs-to-be-Done

### Primary
- **Data Engineers** — profile, validate, transform, map source data into trusted canonical models.
- **Analytics Engineers** — produce clean, consistent datasets for reporting and semantic layers.
- **AI Platform Engineers** — supply canonical, validated data to agents, RAG, ML pipelines.
- **Customer Implementation Engineers** — onboard many customers with different schemas without bespoke code each time.
- **Startup Engineering Teams** — lightweight infra for onboarding, mapping, validation.

### Secondary
Solutions architects · Data product managers · Integration engineers · ML engineers · Customer-success engineers · Enterprise platform teams · Open-source contributors.

**Representative JTBD:** *"When a new customer sends me a CSV/Parquet/table, I want CanonIQ to tell me which fields map to my canonical model, how sure it is and why, and give me validation rules and a clean canonical file — so I can onboard in minutes instead of days and catch drift on the next load."*

---

## 6. Product Principles

1. **Domain-agnostic core.** No industry hardcoding. Core works on generic concepts: `SourceDataset`, `SourceField`, `CanonicalSchema`, `CanonicalEntity`, `CanonicalField`, `MappingSuggestion`, `ValidationRule`, `DriftReport`. Domain behavior comes from canonical-schema YAML and optional domain packs.
2. **Source-agnostic.** Data access is isolated behind connectors. The mapping engine never knows whether data came from CSV, Postgres, BigQuery, S3, or Salesforce.
3. **Local-first by default.** No source data, schemas, sample values, or mappings leave the machine. No telemetry. No external API calls in the core package.
4. **Optional, pluggable AI.** MVP ships rule-based matching plus an AI adapter *interface*. External AI is opt-in and explicit.
5. **Explainability.** Every suggestion includes `confidence`, `status`, `reasons`, and the raw `signals`.
6. **Safe automation.** High confidence → auto-approve; medium → review; low → unmapped. Thresholds configurable.
7. **Versioned canonical models.** Every schema carries `domain`, `entity`, `version`.
8. **Open-source professionalism.** README, LICENSE, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY, CHANGELOG, docs, tests, CI, Dockerfile, examples.

---

## 7. System Architecture

```text
                 ┌──────────────────────────────────────────────────────┐
                 │                       CanonIQ                          │
                 │                                                        │
  data sources   │   ┌────────────┐   records[]   ┌──────────────┐       │
  (files, DBs,   │   │ Connector  │ ────────────▶ │  Profiler    │       │
  warehouses,    │   │ (data      │   + metadata  │ (structure & │       │
  lakes, APIs)   │   │  access)   │               │  statistics) │       │
                 │   └────────────┘               └──────┬───────┘       │
                 │                                        │ SourceProfile │
                 │                                        ▼               │
                 │   CanonicalSchema ──▶ ┌────────────────────────────┐  │
                 │   (versioned YAML)    │      Matching Engine        │  │
                 │                       │ alias·name·type·pattern·    │  │
                 │                       │ range·domain (+opt semantic)│  │
                 │                       └──────────┬─────────────────┘  │
                 │                                  │ MappingSuggestion[] │
                 │            ┌─────────────────────┼─────────────────┐  │
                 │            ▼                     ▼                 ▼  │
                 │   ┌──────────────┐     ┌──────────────┐   ┌──────────┐│
                 │   │ Validation   │     │ Transformer  │   │ Drift    ││
                 │   │ Rule Gen     │     │ (→canonical) │   │ Detector ││
                 │   └──────────────┘     └──────────────┘   └──────────┘│
                 └──────────────────────────────────────────────────────┘
                          │              │              │            │
                   validation_rules  canonical_out  drift_report  suggestions
```

**Separation of concerns:**
- **Connectors** — *only* fetch/sample data; return `List[Dict[str, Any]]` + metadata.
- **Profilers** — turn records + metadata into a `SourceProfile`; format-agnostic.
- **Matchers** — combine signals into scored suggestions; source- and domain-agnostic.
- **Validation / Transform / Drift** — consume the canonical schema + suggestions + profile.

This boundary is the design's load-bearing invariant: adding a new source type must never require touching the matching engine.

---

## 8. Core Data Models

Models are implemented with **Pydantic v2** (`BaseModel`, frozen where practical for immutability). All public outputs serialize to stable JSON. Types shown below are normative.

```python
# canoniq/core/models.py  (illustrative; Pydantic v2)

class SourceFieldProfile(BaseModel):
    name: str
    inferred_type: str                 # see Type System
    null_rate: float                   # 0.0–1.0
    unique_rate: float                  # 0.0–1.0
    sample_values: list[str]
    patterns: list[str]                # see Pattern Detection
    min: float | None = None
    max: float | None = None
    avg_str_len: float | None = None
    distinct_count: int | None = None
    enum_candidates: list[str] | None = None   # if low-cardinality
    pii_flags: list[str] = []          # e.g. ["email", "name", "national_id"]
    position: int | None = None        # column order in source

class SourceProfile(BaseModel):
    source_metadata: dict              # type, path/table, format, row counts...
    row_count_sampled: int
    fields: list[SourceFieldProfile]
    profiler_version: str
    created_at: str                    # ISO 8601 UTC

class CanonicalField(BaseModel):
    name: str
    type: str
    required: bool = False
    description: str | None = None
    aliases: list[str] = []
    min: float | None = None
    max: float | None = None
    enum: list[str] | None = None      # allowed values / code set
    unit: str | None = None            # e.g. "USD", "kg", "ratio_0_1"
    format: str | None = None          # e.g. "iso8601", "e164", "iban", "gtin"
    pii: str | None = None             # none|low|moderate|high|phi
    standard: dict | None = None       # {"name": "FHIR", "path": "Patient.birthDate"}
    semantic_tags: list[str] = []      # e.g. ["identifier", "timestamp", "money"]

class CanonicalEntity(BaseModel):
    domain: str
    entity: str
    version: int
    primary_key: list[str] = []
    fields: dict[str, CanonicalField]

class MappingSuggestion(BaseModel):
    source_field: str
    canonical_field: str | None        # None when unmapped
    confidence: float                  # 0.0–1.0
    status: str                        # auto_approved|requires_review|low_confidence|unmapped
    reasons: list[str]                 # human-readable
    signals: dict                      # {alias, name, type, pattern, range, semantic}

class ValidationRule(BaseModel):
    field: str
    rule: str                          # not_null|valid_email|range|unique|...
    severity: str                      # error|warning|info
    params: dict = {}

class DriftReport(BaseModel):
    status: str                        # no_drift|drift_detected
    missing_fields: list[str]          # previously mapped, now absent
    new_fields: list[str]
    type_changes: list[dict]           # {field, old_type, new_type}
    unmapped_required: list[str]       # required canonical fields no longer mapped
    suggested_remappings: list[dict]   # {source_field, canonical_field, confidence}
    created_at: str
```

> **Enhancement vs. original:** added `unit`, `format`, `pii`, `standard`, `semantic_tags`, `enum` on `CanonicalField`; added `pii_flags`, `enum_candidates`, `distinct_count`, `position` on profiles; added `primary_key` on entities; added `unmapped_required` to drift. These make schemas production-meaningful and make scoring/validation/PII handling first-class.

---

## 9. Canonical Schema Format (Production-Grade)

Canonical schemas are domain-flexible YAML carrying `domain`, `entity`, `version`, an optional `primary_key`, and per-field metadata. The format is a **superset** of the original — every original schema still loads; new keys are optional.

```yaml
domain: retail
entity: product
version: 1
primary_key: [product_id]
standards:                      # optional: declares which standards this entity tracks
  - GS1 GTIN
  - schema.org/Product
fields:
  product_id:
    type: string
    required: true
    description: Unique product identifier; GTIN-14 when available
    format: gtin                # validates GTIN-8/12/13/14 check digit when present
    semantic_tags: [identifier]
    standard: { name: "GS1", path: "GTIN" }
    aliases: [sku, sku_id, item_id, product_sku, gtin, upc, ean]
  product_name:
    type: string
    required: true
    description: Product display name
    standard: { name: "schema.org", path: "Product.name" }
    aliases: [item_name, title, product_title, name]
  price:
    type: decimal
    required: false
    min: 0.0
    unit: "{price_currency}"    # paired with a currency field
    semantic_tags: [money]
    aliases: [sale_price, unit_price, list_price, amount]
  price_currency:
    type: currency_code         # ISO 4217 alpha-3
    required: false
    format: iso4217
    enum: [USD, EUR, GBP, CAD, AUD, JPY]   # illustrative subset; full set validated by format
    aliases: [currency, currency_code, ccy]
  inventory_quantity:
    type: integer
    required: false
    min: 0
    aliases: [available_qty, quantity_available, stock_on_hand, stock_qty]
```

**Field metadata keys:** `type`, `required`, `description`, `aliases`, `min`, `max`, `enum`, `unit`, `format`, `pii`, `standard`, `semantic_tags`.

**`format` validators (built-in, local):** `iso8601`, `date`, `iso4217`, `iso3166_alpha2`, `e164` (phone), `email` (RFC 5322 subset), `uuid` (RFC 4122), `iban` (ISO 13616 checksum), `bic` (ISO 9362), `gtin` (GS1 check digit), `npi` (Luhn), `lei` (ISO 17442). Unknown formats degrade gracefully to type-only validation.

---

## 10. Reference Canonical Schemas by Domain

These upgrade the original examples to reference the standards used in production. **All example data is synthetic.** Healthcare/finance fields are modeled after the public standards' field semantics — not copied from any real record.

### 10.1 Higher Education — Student
*Standards aligned: 1EdTech **OneRoster** (`users`/`students`), **Ed-Fi** Student domain, **CEDS** elements, **Caliper** for LMS activity.*

```yaml
domain: higher_ed
entity: student
version: 1
primary_key: [student_id]
standards: ["1EdTech OneRoster 1.2", "Ed-Fi", "CEDS"]
fields:
  student_id:
    type: string
    required: true
    semantic_tags: [identifier]
    standard: { name: "OneRoster", path: "user.sourcedId" }
    aliases: [banner_id, emplid, person_uid, student_number, sis_id]
  email:
    type: email
    required: true
    format: email
    pii: moderate
    standard: { name: "OneRoster", path: "user.email" }
    aliases: [student_email, email_address, primary_email]
  given_name:
    type: string
    required: false
    pii: moderate
    standard: { name: "OneRoster", path: "user.givenName" }
    aliases: [first_name, fname, given]
  family_name:
    type: string
    required: false
    pii: moderate
    standard: { name: "OneRoster", path: "user.familyName" }
    aliases: [last_name, lname, surname, family]
  gpa:
    type: decimal
    required: false
    min: 0.0
    max: 4.0
    unit: ratio_gpa_4
    standard: { name: "CEDS", path: "Cumulative Grade Point Average" }
    aliases: [cumulative_gpa, overall_gpa, term_gpa]
  enrollment_status:
    type: string
    required: false
    enum: [active, inactive, graduated, withdrawn, leave_of_absence]
    standard: { name: "Ed-Fi", path: "StudentSchoolAssociation.entryGradeLevel" }
    aliases: [status, enrolment_status, student_status]
  last_lms_login:
    type: timestamp
    required: false
    format: iso8601
    standard: { name: "Caliper", path: "SessionEvent.startedAtTime" }
    aliases: [last_activity_at, canvas_last_seen, last_login_date]
```

### 10.2 Retail / E-commerce — Product
*Standards aligned: **GS1 GTIN** (UPC/EAN), **schema.org/Product**, **ISO 4217** (currency), **GLN** for locations.* (See §9 for the full annotated example.)

```yaml
domain: retail
entity: product
version: 1
primary_key: [product_id]
standards: ["GS1 GTIN", "schema.org/Product", "ISO 4217"]
fields:
  product_id:   { type: string, required: true, format: gtin, semantic_tags: [identifier],
                  aliases: [sku, sku_id, item_id, product_sku, gtin, upc, ean] }
  product_name: { type: string, required: true,
                  aliases: [item_name, product_title, title, name] }
  brand:        { type: string, required: false, standard: { name: "schema.org", path: "Product.brand" },
                  aliases: [brand_name, manufacturer, mfr] }
  price:        { type: decimal, required: false, min: 0.0, unit: "{price_currency}", semantic_tags: [money],
                  aliases: [sale_price, unit_price, list_price] }
  price_currency: { type: currency_code, required: false, format: iso4217,
                    aliases: [currency, currency_code, ccy] }
  inventory_quantity: { type: integer, required: false, min: 0,
                        aliases: [available_qty, stock_qty, stock_on_hand] }
```

### 10.3 Healthcare — Patient
*Standards aligned: **HL7 FHIR R4** `Patient` (+ US Core), identifiers per FHIR `identifier` types (MR = Medical Record Number, NPI for providers), **ICD-10-CM** / **SNOMED CT** for diagnosis codes, **LOINC** for labs.* **Synthetic data only — no real PHI.**

```yaml
domain: healthcare
entity: patient
version: 1
primary_key: [patient_id]
standards: ["HL7 FHIR R4 Patient", "US Core", "ICD-10-CM", "SNOMED CT"]
fields:
  patient_id:
    type: string
    required: true
    pii: phi
    semantic_tags: [identifier]
    standard: { name: "FHIR", path: "Patient.identifier[type=MR].value" }
    aliases: [patient_mrn, mrn, patient_number, medical_record_number]
  date_of_birth:
    type: date
    required: false
    format: date
    pii: phi
    standard: { name: "FHIR", path: "Patient.birthDate" }
    aliases: [dob, birth_date, birthdate]
  gender:
    type: string
    required: false
    enum: [male, female, other, unknown]
    standard: { name: "FHIR", path: "Patient.gender" }
    aliases: [sex, administrative_gender]
  email:
    type: email
    required: false
    format: email
    pii: phi
    standard: { name: "FHIR", path: "Patient.telecom[system=email].value" }
    aliases: [patient_email, contact_email]
  condition_code:
    type: string
    required: false
    description: Diagnosis code; ICD-10-CM or SNOMED CT
    standard: { name: "FHIR", path: "Condition.code.coding" }
    aliases: [icd_code, dx_code, diagnosis, diagnosis_code, icd10_code, snomed_code]
```

### 10.4 Finance — Transaction
*Standards aligned: **ISO 20022** (payment message semantics; e.g. `pacs.008`/`camt.053`), **ISO 4217** currency, **IBAN** (ISO 13616) / **BIC** (ISO 9362) account identifiers, **ISO 8601** timestamps, **LEI** (ISO 17442) for entities.*

```yaml
domain: finance
entity: transaction
version: 1
primary_key: [transaction_id]
standards: ["ISO 20022", "ISO 4217", "ISO 13616 IBAN", "ISO 8601"]
fields:
  transaction_id:
    type: string
    required: true
    semantic_tags: [identifier]
    standard: { name: "ISO 20022", path: "TxId / EndToEndId" }
    aliases: [txn_id, transaction_ref, payment_id, end_to_end_id]
  account_id:
    type: string
    required: true
    description: Account identifier; IBAN where applicable
    format: iban
    pii: moderate
    semantic_tags: [identifier]
    standard: { name: "ISO 13616", path: "DbtrAcct.Id.IBAN" }
    aliases: [acct_num, account_number, acct_id, iban]
  amount:
    type: decimal
    required: true
    semantic_tags: [money]
    unit: "{amount_currency}"
    standard: { name: "ISO 20022", path: "Amt.InstdAmt" }
    aliases: [txn_amt, payment_amount, value]
  amount_currency:
    type: currency_code
    required: true
    format: iso4217
    standard: { name: "ISO 4217", path: "Amt.@Ccy" }
    aliases: [currency, ccy, currency_code]
  direction:
    type: string
    required: false
    enum: [debit, credit]
    standard: { name: "ISO 20022", path: "CdtDbtInd (DBIT/CRDT)" }
    aliases: [cdtdbtind, dc_indicator, drcr]
  booking_datetime:
    type: timestamp
    required: true
    format: iso8601
    standard: { name: "ISO 20022", path: "BookgDt / ValDt" }
    aliases: [txn_date, payment_date, posted_at, value_date]
```

### 10.5 Logistics — Shipment
*Standards aligned: **GS1 SSCC** (Serial Shipping Container Code) for shipment units, **SCAC** carrier codes, **ISO 8601** timestamps, **Incoterms** for terms of delivery, **ISO 3166** for country.*

```yaml
domain: logistics
entity: shipment
version: 1
primary_key: [shipment_id]
standards: ["GS1 SSCC", "SCAC", "ISO 8601", "ISO 3166"]
fields:
  shipment_id:
    type: string
    required: true
    semantic_tags: [identifier]
    standard: { name: "GS1", path: "SSCC" }
    aliases: [shipment_no, shipment_number, load_id, sscc]
  tracking_number:
    type: string
    required: false
    semantic_tags: [identifier]
    aliases: [tracking_num, carrier_tracking_id, pro_number]
  carrier_scac:
    type: string
    required: false
    description: Standard Carrier Alpha Code (2–4 letters)
    standard: { name: "SCAC", path: "Carrier SCAC" }
    aliases: [carrier, carrier_name, shipping_provider, scac]
  origin_postal_code:
    type: string
    required: false
    format: postal_code
    aliases: [origin_zip, from_zip, ship_from_postal]
  destination_country:
    type: string
    required: false
    format: iso3166_alpha2
    standard: { name: "ISO 3166", path: "Country alpha-2" }
    aliases: [dest_country, ship_to_country, country]
  estimated_delivery_at:
    type: timestamp
    required: false
    format: iso8601
    aliases: [delivery_eta, eta, expected_delivery_time]
```

### 10.6 HR & Workforce — Employee (domain pack example)
*Standards aligned: **HR Open Standards** (formerly HR-XML), **SOC** / **ISCO-08** occupation codes, **ISO 8601** dates.*

```yaml
domain: hr
entity: employee
version: 1
primary_key: [employee_id]
standards: ["HR Open Standards", "SOC", "ISO 8601"]
fields:
  employee_id:   { type: string, required: true, semantic_tags: [identifier],
                   aliases: [emp_id, worker_id, personnel_number, emplid] }
  work_email:    { type: email, required: false, format: email, pii: moderate,
                   aliases: [email, company_email, business_email] }
  job_code:      { type: string, required: false, standard: { name: "SOC", path: "Occupation Code" },
                   aliases: [soc_code, occupation_code, position_code] }
  hire_date:     { type: date, required: false, format: date,
                   aliases: [start_date, date_of_hire, employment_start] }
  department:    { type: string, required: false,
                   aliases: [dept, department_name, org_unit, cost_center] }
```

> **Domain coverage:** higher-ed, retail, healthcare, finance, logistics ship as MVP examples. HR, insurance, and marketplace ship as documented domain-pack templates. Other entities named in the original PRD (Course, Enrollment, Order, Encounter, Provider, Carrier, Account, etc.) are supported by the *same* schema format — add a YAML file, no code changes.

---

## 11. Type System & Inference

### 11.1 Canonical types

`string` · `text` · `integer` · `decimal` · `boolean` · `date` · `timestamp` · `email` · `currency_code` · `percentage` · `json` · `array` · `unknown`

> Added vs. original: `currency_code`, `percentage`, `json`, `array`. These appear constantly in production data (money, rates, nested API payloads, multi-valued tags).

### 11.2 Inference rules (ordered; first match wins)

1. Email regex (RFC 5322 subset) → `email`
2. ISO-4217 alpha-3 token from a known set → `currency_code`
3. Integer parse (no decimal point, fits int64) → `integer`
4. Float/decimal parse → `decimal`
5. Value in `{true,false,yes,no,y,n,0,1,t,f}` (case-insensitive) → `boolean`
6. Common date formats (`YYYY-MM-DD`, `MM/DD/YYYY`, etc.) → `date`
7. Common datetime / ISO-8601 formats → `timestamp`
8. Parses as JSON object/array → `json` / `array`
9. Trailing `%` or 0–1/0–100 ratio heuristic on a numeric field → `percentage`
10. High average length / free-text → `text`
11. Else → `string`; if column is empty/all-null → `unknown`

Inference operates on the **sampled** values, records the winning rule, and exposes a per-field confidence so the matcher can weight type signals appropriately.

---

## 12. Pattern & PII Detection

### 12.1 Patterns (multi-domain)

`email` · `identifier_like` · `uuid_like` · `decimal` · `integer` · `range_0_to_1` · `range_0_to_4` · `positive_number` · `timestamp_iso` · `date` · `mostly_unique` · `enum_like` · `high_null_rate` · `currency_like` · `currency_code_like` · `postal_code_like` · `phone_like` · `iban_like` · `gtin_like` · `country_code_like`

> Added vs. original: `range_0_to_1`, `currency_code_like`, `iban_like`, `gtin_like`, `country_code_like`. These directly support the upgraded schemas.

### 12.2 PII / PHI detection (local, heuristic)

The profiler flags fields whose name or values match PII/PHI signals and records them in `pii_flags`: `email`, `phone`, `name`, `national_id`, `dob`, `address`, `mrn`, `account_number`, `ip_address`. Profiles **never** emit full raw values for high-PII fields — `sample_values` are redacted/masked (e.g., `a***@***.com`) when a high/PHI flag fires. This is on by default and configurable.

---

## 13. Matching Engine & Confidence Scoring

The engine combines independent **signals**, each normalized to 0.0–1.0:

1. **alias_score** — exact/normalized match against canonical `aliases` (and the canonical name itself).
2. **name_score** — fuzzy similarity (RapidFuzz) between normalized source and canonical names.
3. **type_score** — compatibility between inferred source type and canonical type (with a compatibility matrix, e.g., `integer`→`decimal` is partial).
4. **pattern_score** — overlap between detected patterns and canonical `format`/`semantic_tags`.
5. **range_score** — whether observed min/max fall within canonical `min`/`max`.
6. **semantic_score** *(optional, future/AI adapter)* — embedding similarity; **0 and excluded by default**.

### 13.1 Confidence formula (default weights, configurable)

```text
confidence = clamp(
    0.40 * alias_score +
    0.20 * name_score  +
    0.15 * type_score  +
    0.15 * pattern_score +
    0.10 * range_score,
    0.0, 1.0)
```

When the optional semantic signal is enabled, weights renormalize (the engine reads weights from config so the sum stays 1.0). Each suggestion records the per-signal contributions in `signals` and the human-readable drivers in `reasons` (e.g., *"`sku_id` is a declared alias of `product_id` (alias=1.0); types compatible (string→string)"*).

### 13.2 Status thresholds (configurable)

```text
confidence >= 0.90          -> auto_approved
0.70 <= confidence < 0.90   -> requires_review
confidence < 0.70           -> low_confidence
(no candidate above floor)  -> unmapped
```

### 13.3 Assignment constraints

- A canonical field is mapped by **at most one** source field (best candidate wins; ties broken by alias > name > position).
- Unresolved sources remain `unmapped` and are surfaced (they may indicate new canonical fields or drift).
- The engine is deterministic given the same inputs and config (important for tests and drift comparisons).

---

## 14. Validation Rule Generation

Rules are derived from the canonical schema + the source profile. Each rule has `field`, `rule`, `severity`, `params`.

| Trigger | Rule | Default severity |
|---|---|---|
| `required: true` | `not_null` | error |
| type `email` / `format: email` | `valid_email` | error |
| type `date`/`timestamp` / `format: iso8601` | `valid_datetime` | error |
| `format: iso4217` | `valid_currency_code` | error |
| `format: iban` / `gtin` / `npi` / `lei` | `valid_checksum` | error |
| numeric with `min`/`max` | `range` | error |
| `enum` present | `allowed_values` | error |
| profile shows `mostly_unique` + identifier semantics | `unique` | warning |
| `pii: high|phi` | `pii_present` (advisory) | info |
| profile shows `high_null_rate` on a `required` field | `unexpected_nulls` | warning |

Rules serialize to `validation_rules.yml`. A bundled `validator` can apply them to a dataset and emit a pass/fail report (used by demos and tests).

---

## 15. Transformation

`canoniq apply` produces canonical output:

1. Load source data (via connector/profiler).
2. Load mapping suggestions.
3. Use mappings with status `auto_approved` or `approved` (human-promoted).
4. Rename mapped source columns to canonical field names.
5. Drop unmapped source columns **by default** (configurable: `--keep-unmapped`).
6. Preserve/coerce data types toward the canonical type where lossless.
7. Write canonical CSV (and optionally Parquet/JSON in later versions).
8. *(Future)* Optional lineage/metadata columns (`_canoniq_source_field`, `_canoniq_confidence`).

Transformation never silently coerces lossy values; type-coercion failures are reported, not swallowed.

---

## 16. Schema Drift Detection

Drift compares a **new** source against a **previous mapping** + canonical schema and reports:

1. Previously mapped source field now **missing**.
2. **New** source field added.
3. **Type changed** for a previously profiled field.
4. **Required canonical field no longer mapped** (`unmapped_required`).
5. **Suggested remapping** when a new field aliases an orphaned canonical field.

**Example (retail):**

```text
Previous mapping:        New source fields:        Suggested remap:
  sku_id -> product_id     product_sku               product_sku   -> product_id
  available_qty -> inv...  stock_on_hand             stock_on_hand -> inventory_quantity
```

Output is `drift_report.json` with `status: no_drift | drift_detected`. Drift detection is generic across all domains and sources.

---

## 17. Connectors: Multi-Source Architecture

Enterprise mapping rarely comes from CSV alone. CanonIQ uses a **pluggable connector interface** so new sources are added without touching the engine.

```python
# canoniq/connectors/base.py
from abc import ABC, abstractmethod
from typing import Any

class BaseSourceConnector(ABC):
    @abstractmethod
    def test_connection(self) -> bool:
        """Verify the source is reachable."""

    @abstractmethod
    def list_entities(self) -> list[str]:
        """List available tables, files, collections, or entities."""

    @abstractmethod
    def sample(self, entity: str, limit: int = 1000) -> list[dict[str, Any]]:
        """Return a representative sample for profiling."""

    @abstractmethod
    def get_metadata(self, entity: str) -> dict[str, Any]:
        """Return source metadata: table/file name, schema, path, format,
        column types, nullability, comments, row-count estimate (when available)."""
```

All connectors return the common internal format `list[dict[str, Any]]`, so profiling/matching behave identically regardless of source.

### 17.1 MVP implementation rule

- **Fully implement (v0.1):** `CSVConnector`, `JSONConnector`, `JSONLConnector`.
- **Placeholders (v0.1):** `Parquet`, `Excel`, `Postgres`, `MySQL`, `SQLite`, `BigQuery`, `Snowflake`, `Redshift`, `S3`, `GCS`, `AzureBlob`, `RestAPI`. Each placeholder must:
  1. Subclass `BaseSourceConnector`.
  2. Include docstrings describing the planned implementation.
  3. Raise `NotImplementedError` with a clear message naming the target version.
  4. Note the required optional dependency group.

```python
class BigQueryConnector(BaseSourceConnector):
    """Samples rows from a BigQuery table. Requires `canoniq[bigquery]`. Planned: v0.3."""
    def __init__(self, project_id: str, dataset: str, table: str,
                 credentials_path: str | None = None):
        self.project_id, self.dataset, self.table = project_id, dataset, table
        self.credentials_path = credentials_path

    def test_connection(self) -> bool:
        raise NotImplementedError("BigQueryConnector will be implemented in v0.3 (extra: bigquery).")
    # list_entities / sample / get_metadata raise the same NotImplementedError.
```

### 17.2 Source phases

| Phase | Sources |
|---|---|
| 1 — Local files (v0.1) | CSV, JSON, JSONL |
| 2 — Rich files (v0.2) | Parquet, Excel, local folder sampling |
| 3 — Databases (v0.2/0.3) | Postgres, MySQL, SQL Server, SQLite |
| 4 — Cloud warehouses (v0.3) | BigQuery, Snowflake, Redshift, Databricks SQL |
| 5 — Data lakes (v0.3) | S3, GCS, Azure Blob, Delta Lake |
| 6 — SaaS / API (v0.4) | Salesforce, Canvas, Shopify, Stripe, HubSpot, Workday, generic REST/GraphQL |

### 17.3 Sampling strategies

- **Data lakes / folders:** list files under prefix → pick up to `max_files` (default **5**) → read up to `rows_per_file` (default **1000**) → combine → profile. Never load full datasets.
- **Warehouses / databases:** sample with `SELECT * FROM <table> LIMIT <n>` (parameterized; identifiers safely quoted per dialect). Fetch native schema metadata (column name, type, nullability, comment, table, schema, row-count estimate) when available — this improves mapping confidence because canonical-type inference can lean on declared types.

Supported lake formats: CSV, JSON, JSONL, Parquet now; Delta/Avro/ORC future.

---

## 18. Profilers: Source-Agnostic Profiling

```python
# canoniq/profiler/base.py
class BaseProfiler(ABC):
    @abstractmethod
    def profile(self, records: list[dict[str, Any]],
                source_metadata: dict[str, Any]) -> SourceProfile:
        """Profile records into field-level statistics."""
```

The profiler computes: field names, inferred types, null rates, unique rates, sample values (masked for PII), min/max, average string length, distinct counts, patterns, enum candidates, primary-key candidates, PII/PHI candidates, and timestamp formats. **The profiler never cares which source produced the records** — only `records` + `metadata`. When the connector supplies native column types (warehouses/DBs), the profiler reconciles inferred vs. declared types and records both.

---

## 19. Source Configuration & Secrets

CanonIQ accepts either a direct file (`--source`) or a YAML **source config** (`--source-config`).

```yaml
# local CSV
source: { type: csv, path: examples/higher_ed/source_students.csv }
```
```yaml
# BigQuery
source: { type: bigquery, project_id: my-gcp-project, dataset: student_success,
          table: students, sample_limit: 1000 }
```
```yaml
# Snowflake
source: { type: snowflake, account: my_account, warehouse: COMPUTE_WH,
          database: ANALYTICS, schema: PUBLIC, table: CUSTOMERS, sample_limit: 1000 }
```
```yaml
# S3 data lake
source: { type: s3, bucket: my-data-lake, prefix: raw/customers/date=2026-05-29/,
          format: parquet, sample_limit: 1000 }
```
```yaml
# Postgres (secrets via env interpolation — never inline)
source:
  type: postgres
  host: ${POSTGRES_HOST}
  port: ${POSTGRES_PORT}
  database: ${POSTGRES_DB}
  username: ${POSTGRES_USER}
  password: ${POSTGRES_PASSWORD}
  table: customers
  sample_limit: 1000
```

**Security requirement:** credentials must **never** be stored inline. The config loader interpolates `${VAR}` from environment variables (and supports a documented secrets-manager hook). A config containing a literal-looking secret triggers a loader warning.

---

## 20. Output Artifacts (Contracts)

Stable, documented output schemas (so downstream tools can depend on them):

| Artifact | File | Shape |
|---|---|---|
| Source profile | `profile.json` | `SourceProfile` (§8) |
| Mapping suggestions | `suggestions.json` | `{ canonical: {domain, entity, version}, mappings: MappingSuggestion[] }` |
| Validation rules | `validation_rules.yml` | `ValidationRule[]` grouped by field |
| Canonical output | `canonical_<entity>.csv` | renamed/typed columns |
| Drift report | `drift_report.json` | `DriftReport` (§8) |

Every artifact includes `canoniq_version` and `created_at` (ISO 8601 UTC) for reproducibility.

---

## 21. CLI Specification

Built with **Typer + Rich**. All commands accept `--source` (file) or `--source-config` (YAML) where input is required.

```bash
# Profile (file or config)
canoniq profile --source examples/retail/source_products.csv --out profile.json
canoniq profile --source-config examples/sources/bigquery_students.yml --out profile.json

# Suggest mappings
canoniq suggest --profile profile.json \
  --canonical examples/retail/canonical_product.yml --out suggestions.json

# Generate validation rules
canoniq rules --suggestions suggestions.json \
  --canonical examples/retail/canonical_product.yml --out validation_rules.yml

# Apply (transform → canonical)
canoniq apply --source examples/retail/source_products.csv \
  --mapping suggestions.json --out canonical_products.csv

# Drift check
canoniq drift-check --source examples/retail/new_source_products.csv \
  --mapping suggestions.json --canonical examples/retail/canonical_product.yml \
  --out drift_report.json

# Demos (must run the full pipeline end-to-end)
canoniq demo higher-ed | retail | healthcare | finance | logistics
```

Each `demo` must: profile → suggest → generate rules → apply → detect drift → write outputs to an output folder → print a clean success summary (Rich table). Exit codes are non-zero on failure for CI use.

---

## 22. Python SDK Specification

```python
from canoniq import CanonIQ

engine = CanonIQ()                       # local-first; no network by default

# Files
profile = engine.profile_csv("examples/retail/source_products.csv")
# or: engine.profile_json(...), engine.profile_jsonl(...)

# Source config / connectors
profile = engine.profile_source_config("examples/sources/bigquery_students.yml")

from canoniq.connectors import CSVConnector
records = CSVConnector("examples/retail/source_products.csv").sample(entity="default", limit=1000)
profile = engine.profile_records(records)

# Core pipeline (identical for any domain given a canonical schema)
suggestions = engine.suggest_mappings(profile=profile,
    canonical_schema_path="examples/retail/canonical_product.yml")
rules = engine.generate_validation_rules(suggestions=suggestions,
    canonical_schema_path="examples/retail/canonical_product.yml")
canonical_df = engine.apply_mapping(
    source_path="examples/retail/source_products.csv", mapping=suggestions)
drift = engine.detect_drift(
    source_path="examples/retail/new_source_products.csv",
    previous_mapping=suggestions,
    canonical_schema_path="examples/retail/canonical_product.yml")
```

The SDK is the substrate the CLI is built on; both share one engine implementation.

---

## 23. Optional AI Adapter

```python
# canoniq/ai/base.py
class BaseAIMatcher(ABC):
    @abstractmethod
    def semantic_score(self, source_field: SourceFieldProfile,
                       canonical_field: CanonicalField) -> float: ...
```

- MVP ships the interface plus a **no-op/local** default. No external calls unless the user explicitly configures an adapter (e.g., a local `sentence-transformers` model, or an OpenAI/Anthropic adapter installed via an extra).
- When enabled, the `semantic_score` participates as the 6th signal and weights renormalize.
- The README and SECURITY policy must state that enabling an external AI adapter is the *only* path by which data could leave the machine, and that it is opt-in.

---

## 24. Non-Functional Requirements

- **Performance:** profiling a 100k-row local CSV within the default sampling window completes in seconds; sampling caps prevent unbounded reads on lakes/warehouses.
- **Determinism:** identical inputs + config produce identical suggestions and drift reports.
- **Typed:** full type hints; `mypy`/`pyright`-clean core.
- **Modular:** many small files (200–400 lines typical; 800 max), organized by feature/domain.
- **Immutability:** transformations return new objects; no in-place mutation of profiles/suggestions.
- **Errors:** explicit handling at boundaries (file IO, parsing, config); never silently swallow. User-facing messages in CLI; detailed context in logs.
- **Observability:** structured, opt-in local logging; **no telemetry**.

---

## 25. Security & Privacy

`SECURITY.md` must state:

> CanonIQ is local-first by default. CanonIQ does not send source data, schemas, sample values, or mappings to external AI providers unless the user explicitly configures an external AI adapter.

Requirements:

- No telemetry in MVP. No external API calls in the core package.
- No real healthcare, financial, education, or personal data in examples — **all examples synthetic**.
- No API keys or credentials in the repo. Source configs use `${ENV}` interpolation.
- High-PII/PHI sample values are masked in profiles by default.
- A documented vulnerability-disclosure process and supported-versions table.

---

## 26. Technology Stack & Packaging

**Language:** Python 3.10+

**Core (required) dependencies:** `pandas`, `pyyaml`, `pydantic` (v2), `typer`, `rich`, `rapidfuzz`, `pytest` (dev).

**Optional dependency groups** (`pyproject.toml`) — keep the core install lightweight:

```toml
[project.optional-dependencies]
files     = ["openpyxl", "pyarrow"]
databases = ["sqlalchemy", "psycopg2-binary", "pymysql"]
bigquery  = ["google-cloud-bigquery"]
snowflake = ["snowflake-connector-python"]
aws       = ["boto3", "s3fs"]
azure     = ["azure-storage-blob"]
gcp       = ["google-cloud-storage", "google-cloud-bigquery"]
ai        = ["sentence-transformers"]          # local embeddings, opt-in
all       = ["openpyxl","pyarrow","sqlalchemy","psycopg2-binary","pymysql",
             "google-cloud-bigquery","google-cloud-storage",
             "snowflake-connector-python","boto3","s3fs","azure-storage-blob"]
```

```bash
pip install canoniq                 # lightweight core
pip install "canoniq[bigquery]"     # + BigQuery
pip install "canoniq[aws]"          # + S3
```

Optional AI deps are **never** required for core install. Enterprise connectors stay disabled unless their extra is installed.

---

## 27. Repository Structure

```text
canoniq/
├── canoniq/
│   ├── __init__.py
│   ├── engine.py                 # CanonIQ SDK facade
│   ├── config.py                 # thresholds, weights, sampling, secrets
│   ├── cli.py                    # Typer CLI
│   │
│   ├── core/
│   │   ├── models.py             # Pydantic v2 models
│   │   └── constants.py
│   │
│   ├── connectors/               # data access (source-agnostic boundary)
│   │   ├── base.py
│   │   ├── csv_connector.py      # implemented (v0.1)
│   │   ├── json_connector.py     # implemented (v0.1)
│   │   ├── jsonl_connector.py    # implemented (v0.1)
│   │   ├── parquet_connector.py  # placeholder
│   │   ├── excel_connector.py    # placeholder
│   │   ├── postgres_connector.py # placeholder
│   │   ├── mysql_connector.py    # placeholder
│   │   ├── sqlite_connector.py   # placeholder
│   │   ├── bigquery_connector.py # placeholder
│   │   ├── snowflake_connector.py# placeholder
│   │   ├── redshift_connector.py # placeholder
│   │   ├── s3_connector.py       # placeholder
│   │   ├── gcs_connector.py      # placeholder
│   │   ├── azure_blob_connector.py # placeholder
│   │   └── rest_api_connector.py # placeholder
│   │
│   ├── sources/
│   │   └── config_loader.py      # source-config YAML + ${ENV} interpolation
│   │
│   ├── profiler/
│   │   ├── base.py
│   │   ├── profiler.py           # source-agnostic profiling
│   │   ├── type_inference.py
│   │   ├── pattern_detection.py
│   │   └── pii_detection.py
│   │
│   ├── registry/
│   │   ├── canonical_schema.py   # YAML loader + validation
│   │   └── mapping_registry.py
│   │
│   ├── matcher/
│   │   ├── name_matcher.py
│   │   ├── alias_matcher.py
│   │   ├── type_matcher.py
│   │   ├── pattern_matcher.py
│   │   ├── range_matcher.py
│   │   └── mapping_engine.py
│   │
│   ├── scoring/confidence.py
│   ├── validation/{rule_generator.py, validator.py, formats.py}
│   ├── transform/transformer.py
│   ├── drift/drift_detector.py
│   ├── ai/{base.py, optional_ai_matcher.py}
│   └── domains/{higher_ed,retail,healthcare,finance,logistics}.py
│
├── examples/
│   ├── higher_ed/{canonical_student.yml, source_students.csv, new_source_students.csv, demo.py}
│   ├── retail/{canonical_product.yml, source_products.csv, new_source_products.csv, demo.py}
│   ├── healthcare/{canonical_patient.yml, source_patients.csv, new_source_patients.csv, demo.py}
│   ├── finance/{canonical_transaction.yml, source_transactions.csv, new_source_transactions.csv, demo.py}
│   ├── logistics/{canonical_shipment.yml, source_shipments.csv, new_source_shipments.csv, demo.py}
│   └── sources/                  # source-config examples
│       ├── local_csv_students.yml
│       ├── local_json_products.yml
│       ├── postgres_customers.yml
│       ├── bigquery_students.yml
│       ├── snowflake_transactions.yml
│       ├── s3_orders.yml
│       └── gcs_lms_activity.yml
│
├── tests/
│   ├── test_csv_profiler.py        test_json_profiler.py     test_jsonl_connector.py
│   ├── test_type_inference.py      test_pattern_detection.py test_pii_detection.py
│   ├── test_canonical_schema.py    test_format_validators.py
│   ├── test_mapping_engine.py      test_confidence.py
│   ├── test_validation_rules.py    test_transformer.py       test_drift_detector.py
│   ├── test_source_config.py       test_connector_placeholders.py
│   └── test_domain_examples.py     # all 5 domains end-to-end
│
├── docs/
│   ├── architecture.md  quickstart.md  concepts.md  domain_packs.md
│   ├── connectors.md    sources.md     standards_mapping.md  roadmap.md
│   └── {higher_ed,retail,healthcare,finance,logistics}_use_case.md
│
├── .github/workflows/ci.yml
├── README.md  LICENSE  CONTRIBUTING.md  CODE_OF_CONDUCT.md  SECURITY.md  CHANGELOG.md
├── pyproject.toml  .gitignore  Dockerfile
```

---

## 28. Testing Strategy

- **Coverage:** ≥ 80% line coverage; CI fails below threshold.
- **Determinism:** golden-file tests for `suggestions.json` / `drift_report.json` across all 5 domains.
- **Must cover:** CSV/JSON/JSONL profiling; type inference; pattern + PII detection; canonical schema loading + format validators; mapping confidence + status gating; validation-rule generation; transformation (incl. type coercion + unmapped drop); drift detection (missing/new/type-change/unmapped-required/remap); source-config loading + `${ENV}` interpolation; connector placeholders raising `NotImplementedError`.
- **Network isolation:** tests must make **zero** external network calls (enforced; e.g., socket guard in CI).
- **Synthetic data only.**

---

## 29. Documentation Requirements

- **README.md** — positions CanonIQ as domain- and source-agnostic; use cases for higher-ed, retail, healthcare, finance, logistics, SaaS onboarding, AI agent platforms; quickstart; install matrix (core vs. extras).
- **docs/standards_mapping.md** *(new)* — table mapping each domain's canonical fields to the production standards they track (FHIR, ISO 20022, GS1, OneRoster/Ed-Fi/CEDS, HR Open, ISO/RFC primitives).
- **docs/domain_packs.md** — how to add a domain: (1) create canonical schema YAML, (2) add aliases, (3) add synthetic example data, (4) add tests, (5) add `demo` support.
- **docs/connectors.md** *(new)* — how to add a connector (subclass `BaseSourceConnector`, declare extra, return common format).
- **docs/sources.md** *(new)* — source-config format, secrets via env, sampling strategy.
- **docs/higher_ed_use_case.md** — keep higher-ed (e.g., a Risely-style scenario) as **one example only**, not the whole product.

---

## 30. Roadmap

| Version | Theme | Highlights |
|---|---|---|
| **v0.1** | MVP core | Generic engine; CSV/JSON/JSONL connectors; type/pattern/PII profiling; matching + scoring + explanations; validation; transform; drift; CLI + SDK; 5 domain examples; source-config; placeholder connectors; CI/Docker/docs |
| **v0.2** | Rich files + DBs | Parquet, Excel, folder sampling; Postgres, MySQL, SQLite (real); approved-mapping promotion workflow (CLI) |
| **v0.3** | Cloud warehouses + lakes | BigQuery, Snowflake, Redshift, Databricks; S3, GCS, Azure Blob; native metadata-assisted matching |
| **v0.4** | SaaS / API | Salesforce, Canvas, Shopify, Stripe, HubSpot, Workday, generic REST/GraphQL |
| **Future** | Server/API mode · review UI · semantic AI matching (local + hosted adapters) · lineage/metadata columns · domain packs as installable distributions |

---

## 31. Acceptance Criteria

The MVP (v0.1.0) is complete when:

```bash
pip install -e .
pytest                      # ≥80% coverage, zero network calls
canoniq demo higher-ed
canoniq demo retail
canoniq demo healthcare
canoniq demo finance
canoniq demo logistics

# Source input works both ways:
canoniq profile --source examples/higher_ed/source_students.csv --out profile.json
canoniq profile --source-config examples/sources/local_csv_students.yml --out profile_from_config.json
```

And:

- Each demo runs the full pipeline (profile → suggest → rules → apply → drift), writes outputs, and prints a clean success summary.
- Placeholder connectors (BigQuery, Snowflake, Redshift, Postgres, MySQL, S3, GCS, Azure Blob, REST API) follow `BaseSourceConnector`, carry docstrings, raise clear `NotImplementedError` with target version + required extra.
- Canonical schemas load with the production-grade format (standards/format/pii/unit/enum keys) and the bundled standards mapping doc is present.
- No external network calls during tests; all example data synthetic; no secrets in repo.

---

## 32. Build Plan for Claude Code

Build CanonIQ as a production-quality, open-source Python project. **Do not make it education-specific** — higher education is one domain example only.

1. Create the repo structure (§27) and `pyproject.toml` with optional dependency groups (§26).
2. Implement generic core models (Pydantic v2, §8).
3. Implement `BaseSourceConnector` and the **real** local connectors: CSV, JSON, JSONL.
4. Implement placeholder enterprise connectors (Parquet, Excel, SQLite, Postgres, MySQL, BigQuery, Snowflake, Redshift, S3, GCS, Azure Blob, REST API) per §17.1.
5. Implement the source-config loader with `${ENV}` interpolation + secret-leak warnings (§19).
6. Implement the canonical-schema YAML loader + validation, supporting the production-grade format (§9).
7. Implement the source-agnostic profiler: type inference (§11), pattern detection + PII masking (§12).
8. Implement matchers (alias/name/type/pattern/range), the mapping engine, and confidence scoring with configurable weights/thresholds (§13).
9. Implement validation-rule generation + format validators (§14) and the validator.
10. Implement the transformer (§15) and drift detector (§16).
11. Implement the `CanonIQ` SDK facade (§22) and the Typer CLI with `--source`/`--source-config` (§21).
12. Add the five domain examples with **production-standard canonical schemas** (§10) and synthetic source data + `new_source` variants for drift.
13. Add source-config examples (§27) and the optional AI adapter interface + no-op default (§23).
14. Add unit + end-to-end tests for all domains with golden files and network isolation (§28).
15. Add README, docs (incl. `standards_mapping.md`, `connectors.md`, `sources.md`), SECURITY.md, CONTRIBUTING.md, CODE_OF_CONDUCT.md, CHANGELOG.md.
16. Add GitHub Actions CI (lint, type-check, test+coverage, no-network guard) and a Dockerfile.

The MVP must be local-first, privacy-conscious, typed, tested, modular, and ready to push to GitHub.

---

## 33. Glossary & Standards Reference

| Domain | Standard | What CanonIQ uses it for |
|---|---|---|
| Healthcare | **HL7 FHIR R4** (`Patient`, `Encounter`, `Condition`, `Observation`, `Claim`), **US Core** | Canonical entity/field semantics & identifier types |
| Healthcare | **ICD-10-CM**, **SNOMED CT**, **CPT/HCPCS**, **LOINC**, **NPI** | Diagnosis/procedure/lab/provider code sets |
| Finance | **ISO 20022** (`pacs`/`camt`/`pain`) | Payment/transaction field semantics |
| Finance | **ISO 4217**, **IBAN (ISO 13616)**, **BIC (ISO 9362)**, **LEI (ISO 17442)** | Currency, account, entity identifiers |
| Retail | **GS1 GTIN** (UPC/EAN), **GLN**, **schema.org/Product** | Product identity & catalog fields |
| Logistics | **GS1 SSCC**, **SCAC**, **Incoterms** | Shipment identity, carrier codes, delivery terms |
| Higher-ed | **1EdTech OneRoster**, **Ed-Fi**, **CEDS**, **Caliper**, **PESC** | Student/roster/activity field semantics |
| HR | **HR Open Standards**, **SOC / ISCO-08** | Worker fields & occupation codes |
| Cross-cutting | **ISO 8601** (datetime), **ISO 3166** (country), **E.164** (phone), **RFC 5322** (email), **RFC 4122** (UUID) | Primitive format validators |

**Key terms:** *Canonical schema* — the target model fields map into. *Connector* — data-access adapter. *Profiler* — computes field statistics. *Mapping suggestion* — a scored, explained source→canonical proposal. *Drift* — divergence between a new source and a prior mapping/schema.

---

*End of PRD. This document supersedes the two source PDFs and is the authoritative build specification for CanonIQ v0.1.0.*
