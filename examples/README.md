# Examples & sample use-cases

Every example here uses **synthetic data only**. Nothing leaves your machine —
CanonIQ is local-first and makes no network calls in the core package.

## Runnable demos

Each domain folder ships a self-contained `demo.py` that runs the full pipeline
(profile -> suggest -> rules -> transform -> drift) and prints explained mappings:

```bash
python examples/higher_ed/demo.py
python examples/retail/demo.py
python examples/healthcare/demo.py
python examples/finance/demo.py
python examples/logistics/demo.py
```

The same flows are available through the CLI:

```bash
canoniq demo higher-ed
canoniq demo retail
canoniq demo healthcare
canoniq demo finance
canoniq demo logistics
```

## Featured: config-driven auto-onboarding

CanonIQ's **auto-onboarding** workflow maps each *provider's* messy source files
onto shared canonical models, validates them, checks for drift, and produces a
**deployment-readiness score** per provider (no deployment happens — you get a
verdict plus the canonical artifacts a deploy step could consume). A "provider" is
whatever supplies data in your domain; the engine is identical across domains.

Two complete, end-to-end examples ship — same engine, different industry — to prove
the pipeline is domain-agnostic:

| Example | Providers | Outcome spread |
|---|---|---|
| [`higher_ed_auto_onboarding/`](higher_ed_auto_onboarding/README.md) — *CampusLaunch AI* | 3 universities (SIS/LMS/advising exports) | 1 auto · 1 minor-review · 1 blocked |
| [`retail_vendor_onboarding/`](retail_vendor_onboarding/README.md) — *ShelfSync* | 3 retail vendors (product/inventory/order feeds) | 1 auto · 1 minor-review · 1 blocked |

```bash
python examples/higher_ed_auto_onboarding/demo_auto_onboard.py
python examples/retail_vendor_onboarding/demo_auto_onboard.py
# or, via the CLI:
canoniq onboard-batch --config-dir examples/retail_vendor_onboarding/onboarding_configs
```

See the domain-neutral [**Auto-Onboarding Guide**](../docs/onboarding.md) to build
your own pipeline for any field.

## Sample use-cases by domain

| Domain | Canonical entity | Standards tracked | Walkthrough |
|---|---|---|---|
| Higher education | `student` | OneRoster, Ed-Fi, CEDS | [docs/higher_ed_use_case.md](../docs/higher_ed_use_case.md) |
| Retail | `product` | GS1 GTIN, schema.org, ISO 4217 | [docs/retail_use_case.md](../docs/retail_use_case.md) |
| Healthcare | `patient` | HL7 FHIR R4, US Core, ICD-10, SNOMED | [docs/healthcare_use_case.md](../docs/healthcare_use_case.md) |
| Finance | `transaction` | ISO 20022, ISO 4217, IBAN, ISO 8601 | [docs/finance_use_case.md](../docs/finance_use_case.md) |
| Logistics | `shipment` | GS1 SSCC, SCAC, ISO 3166, ISO 8601 | [docs/logistics_use_case.md](../docs/logistics_use_case.md) |

Cross-cutting use-cases (SaaS onboarding, AI agent platforms) are covered in the
top-level [README](../README.md#use-cases).

## Files in each domain folder

- `canonical_<entity>.yml` — the versioned canonical schema (the mapping target).
- `source_<entity>.(csv|json)` — a synthetic source feed with different column names.
- `new_source_<entity>.csv` — a later ingestion that diverges, to exercise drift.
- `demo.py` — runnable end-to-end script.

## Source configs

`sources/` holds source-config examples. The two `local_*` configs run offline;
the rest reference placeholder connectors and resolve secrets from `${ENV}`:

```bash
canoniq profile --source-config examples/sources/local_csv_students.yml --out profile.json
```

See [docs/sources.md](../docs/sources.md) for the source-config format.
