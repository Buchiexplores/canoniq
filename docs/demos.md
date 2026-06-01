# Demo Walkthroughs (STAR)

Each bundled demo runs CanonIQ's **full pipeline** against synthetic data for one
domain and prints what it found. This guide frames every demo with **STAR** —
**S**ituation, **T**ask, **A**ction, **R**esult — so you can see the real-world
problem each one solves, not just the table it prints.

> Run any demo yourself — the demo datasets ship inside the package, so this works
> straight from a `pip install` (no clone required):
>
> ```bash
> pip install canoniq
> canoniq demo higher-ed   # or: retail · healthcare · finance · logistics
> ```
>
> Every `canoniq demo <domain>` is a **comprehensive, narrated walkthrough** —
> use-case framing, the pipeline, field-level mappings *with reasons*, validation
> findings, the transform result, and detailed drift. `higher-ed` goes further still:
> it runs the full **multi-school CampusLaunch AI auto-onboarding** demonstration
> (3 schools, readiness scoring, portfolio roll-up, ROI).
>
> Outputs are written to `out/<entity>/` (`profile.json`, `suggestions.json`,
> `validation_rules.yml`, `canonical_<entity>.csv`, `drift_report.json`).

## How to read the output

Every demo prints two things: a **mappings table** and a **summary**.

| Column / row | Meaning |
|---|---|
| `source` → `canonical` | the inferred field mapping (source column → your canonical field) |
| `conf` | confidence 0.00–1.00, a weighted blend of alias, name, type, pattern, and range signals |
| `status` | `auto_approved` (≥ 0.90), `requires_review` (0.70–0.90), or `low_confidence` (< 0.70) |
| `mappings (auto/review)` | how many fields cleared the auto bar vs. need a human glance |
| `validation rules` | checks generated from the canonical schema (types, formats, enums, checksums) |
| `drift` | whether the *next* batch diverged from the mapping CanonIQ just learned |

The throughline across every domain: **CanonIQ proposes, explains, and gates — it
never silently guesses.** High-confidence matches are auto-approved; ambiguous ones
are flagged for review; weak ones are held back; and schema changes are caught
before they corrupt downstream data.

---

## 1. Higher education — onboarding a Student Information System export

**Situation.** A university analytics team powers an advising dashboard from a
Banner SIS export. The file uses institution-specific headers (`banner_id`,
`cumulative_gpa`, `last_activity_at`) that mean nothing to the shared `student`
model the dashboard expects.

**Task.** Map the export onto the canonical `student` entity, validate it, and be
ready for next term's export — which never has quite the same columns.

**Action.**
```bash
canoniq demo higher-ed
```

**Result.** CanonIQ profiled 7 fields and mapped all 7 — 3 auto-approved, 4 flagged
for a quick review — generated 7 validation rules, and transformed 10 rows:

| source | → canonical | conf | status |
|---|---|---|---|
| `banner_id` | `student_id` | 0.90 | auto_approved |
| `student_email` | `email` | 0.90 | auto_approved |
| `first_name` | `given_name` | 0.75 | requires_review |
| `last_name` | `family_name` | 0.75 | requires_review |
| `cumulative_gpa` | `gpa` | 0.85 | requires_review |
| `status` | `enrollment_status` | 0.85 | requires_review |
| `last_activity_at` | `last_lms_login` | 0.90 | auto_approved |

**Drift caught:** the follow-up batch dropped `banner_id`/`status` and introduced
`student_number`/`program_code`. CanonIQ flagged the change and **suggested
re-mapping `student_number → student_id` (0.90)** instead of silently losing the
identifier. *Business value: a new school's data is dashboard-ready in seconds, and
schema changes surface as a review item rather than a broken report.*

---

## 2. Retail — normalizing a supplier product feed

**Situation.** A marketplace lists products from hundreds of suppliers. Each feed
names things differently (`sku_id`, `sale_price`, `available_qty`) and prices come
without a clear currency contract.

**Task.** Normalize a supplier catalog onto the canonical `product` model (GS1 GTIN /
schema.org aligned) so items can be listed and priced consistently.

**Action.**
```bash
canoniq demo retail
```

**Result.** 6 fields profiled, all mapped (2 auto-approved, 4 review), 8 validation
rules, 8 rows transformed:

| source | → canonical | conf | status |
|---|---|---|---|
| `sku_id` | `product_id` | 0.82 | requires_review |
| `item_name` | `product_name` | 0.75 | requires_review |
| `brand_name` | `brand` | 0.75 | requires_review |
| `sale_price` | `price` | 1.00 | auto_approved |
| `currency` | `price_currency` | 0.90 | auto_approved |
| `available_qty` | `inventory_quantity` | 0.85 | requires_review |

**Drift caught:** the next feed renamed `sku_id → product_sku` and `sale_price →
list_price`; CanonIQ proposed both remappings (incl. `list_price → price` at 1.00).
*Business value: the 500th supplier onboards as easily as the 1st, and a supplier
quietly renaming a column doesn't silently break pricing.*

---

## 3. Healthcare — aligning an EHR patient extract (with PHI handling)

**Situation.** A clinic integrates a patient extract from its EHR. Columns are terse
(`mrn`, `dob`, `sex`, `icd10_code`) and the data is sensitive — direct identifiers
and clinical codes that must be handled carefully.

**Task.** Map the extract onto a canonical `patient` model (HL7 FHIR R4 / US Core
aligned), validate codes and formats, and keep PHI masked by default.

**Action.**
```bash
canoniq demo healthcare
```

**Result.** 5 fields profiled, all mapped (3 auto-approved, 2 review), 8 validation
rules, 8 rows transformed:

| source | → canonical | conf | status |
|---|---|---|---|
| `mrn` | `patient_id` | 0.90 | auto_approved |
| `dob` | `date_of_birth` | 0.90 | auto_approved |
| `sex` | `gender` | 0.85 | requires_review |
| `patient_email` | `email` | 0.90 | auto_approved |
| `icd10_code` | `condition_code` | 0.75 | requires_review |

**Drift caught:** the next extract switched to FHIR-style names
(`birth_date`, `administrative_gender`, `contact_email`, `snomed_code`); CanonIQ
mapped the equivalents and flagged the coding-system change (ICD-10 → SNOMED) for
clinical review. *Business value: partner feeds align to one model, sensitive values
are masked before they leave the profiler, and a coding-system swap is caught — not
absorbed.*

> PHI/PII note: high-sensitivity sample values are masked by default before they
> leave the profiler. All demo data is synthetic.

---

## 4. Finance — reconciling a bank transaction file

**Situation.** A fintech ingests a partner bank's daily transaction file with
abbreviated headers (`txn_id`, `iban`, `txn_amt`, `drcr`) and must reconcile it into
an ISO 20022-aligned ledger with currency and checksum guarantees.

**Task.** Map the file onto the canonical `transaction` model, validate IBAN/currency/
timestamps, and detect when the bank changes its export format.

**Action.**
```bash
canoniq demo finance
```

**Result.** The cleanest case — 6 fields profiled, 5 auto-approved, only 1 review,
11 validation rules (the most of any demo, incl. IBAN and ISO 4217 checks), 8 rows:

| source | → canonical | conf | status |
|---|---|---|---|
| `txn_id` | `transaction_id` | 0.90 | auto_approved |
| `iban` | `account_id` | 0.90 | auto_approved |
| `txn_amt` | `amount` | 0.90 | auto_approved |
| `currency` | `amount_currency` | 0.90 | auto_approved |
| `drcr` | `direction` | 0.85 | requires_review |
| `posted_at` | `booking_datetime` | 0.90 | auto_approved |

**Drift caught:** the next file fully re-styled its headers (`transaction_ref`,
`account_number`, `payment_amount`, `ccy`, `value_date`); CanonIQ proposed all five
remappings at high confidence. *Business value: clean, standards-backed reconciliation
with checksum validation, and resilience to a bank silently reformatting its feed.*

---

## 5. Logistics — unifying a carrier feed (and knowing when to ask)

**Situation.** A 3PL aggregates shipment feeds from many carriers. Names vary
(`shipment_no`, `tracking_num`, `from_zip`, `eta`) and some columns are genuinely
ambiguous.

**Task.** Unify a carrier feed onto the canonical `shipment` model (GS1 SSCC / SCAC
aligned) and surface anything too uncertain to auto-map.

**Action.**
```bash
canoniq demo logistics
```

**Result.** 6 fields profiled, 3 auto-approved, 2 review, **and 1 deliberately held
back as low-confidence** — exactly the behavior you want:

| source | → canonical | conf | status |
|---|---|---|---|
| `shipment_no` | `shipment_id` | 0.90 | auto_approved |
| `tracking_num` | `tracking_number` | 0.87 | requires_review |
| `carrier` | `carrier_scac` | 0.75 | requires_review |
| `from_zip` | `origin_postal_code` | 0.68 | **low_confidence** |
| `ship_to_country` | `destination_country` | 0.90 | auto_approved |
| `eta` | `estimated_delivery_at` | 0.90 | auto_approved |

**Drift caught:** the next feed renamed nearly everything (`load_id`,
`carrier_tracking_id`, `dest_country`, `expected_delivery_time`); CanonIQ proposed
the remappings and kept the weak ones honest. *Business value: confident mappings
flow through, ambiguous ones (`from_zip → origin_postal_code`) are escalated instead
of guessed — the difference between a trustworthy pipeline and a silent data bug.*

---

## From demo to production: config-driven auto-onboarding

The single-file demos show the pipeline. The **auto-onboarding** examples show the
same engine scaled to *many providers with a deployment-readiness verdict* — the
natural next step for an enterprise rollout:

| Example | STAR in one line |
|---|---|
| [Higher-ed auto-onboarding](../examples/higher_ed_auto_onboarding/README.md) | **S**: a platform onboarding many universities · **T**: decide which are deploy-ready · **A**: `canoniq onboard-batch` · **R**: 1 auto-deploy, 1 review, 1 blocked, each with a reason |
| [Retail vendor auto-onboarding](../examples/retail_vendor_onboarding/README.md) | **S**: a marketplace onboarding many vendors · **T**: gate each vendor's feeds · **A**: `canoniq onboard-batch` · **R**: scored readiness per vendor, full audit trail |

See the [Auto-Onboarding Guide](onboarding.md) to build one for your own domain.

## Where to go next

- [Quickstart](quickstart.md) — install and your first pipeline
- [Concepts](concepts.md) — how profiling, matching, scoring, and drift work
- [Standards mapping](standards_mapping.md) — canonical fields ↔ industry standards
- Per-domain deep dives: [higher-ed](higher_ed_use_case.md) · [retail](retail_use_case.md) · [healthcare](healthcare_use_case.md) · [finance](finance_use_case.md) · [logistics](logistics_use_case.md)
