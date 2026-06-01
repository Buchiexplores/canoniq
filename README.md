# CanonIQ

[![PyPI](https://img.shields.io/pypi/v/canoniq.svg)](https://pypi.org/project/canoniq/)
[![CI](https://github.com/Buchiexplores/canoniq/actions/workflows/ci.yml/badge.svg)](https://github.com/Buchiexplores/canoniq/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](pyproject.toml)
[![Coverage](https://img.shields.io/badge/coverage-92%25-brightgreen.svg)](#development)
[![Code style: ruff](https://img.shields.io/badge/lint-ruff-261230.svg)](https://github.com/astral-sh/ruff)
[![Typed](https://img.shields.io/badge/typed-mypy-blue.svg)](https://mypy-lang.org/)

**AI-Powered Canonical Mapping Engine — map messy source data into trusted canonical models.**

CanonIQ profiles a source dataset, loads a versioned canonical schema, and proposes
**scored, explained source→canonical field mappings**. It then generates validation rules,
transforms data into the canonical shape, and detects schema drift when a new ingestion arrives.

CanonIQ is **domain-agnostic** and **source-agnostic**. Higher education is one bundled example —
not the product. The same engine maps retail catalogs, healthcare patient records, financial
transactions, and logistics shipments against their respective industry standards.

> **Local-first by default.** CanonIQ does not send your source data, schemas, sample values, or
> mappings to any external service. There is no telemetry. Network access only ever happens if you
> explicitly configure an optional external AI adapter.

---

## Why CanonIQ

Onboarding external data means reconciling someone else's column names, types, and conventions
with your own canonical model. That work is repetitive, error-prone, and hard to audit. CanonIQ
turns it into a deterministic, explainable pipeline:

- **Profile** any source (CSV / JSON / JSONL today) — inferred types, patterns, PII flags.
- **Suggest** mappings with a confidence score and human-readable reasons per field.
- **Gate** suggestions into `auto_approved` / `requires_review` / `low_confidence`.
- **Validate** with generated rules including format checksums (IBAN, GTIN, NPI, LEI…).
- **Transform** to the canonical output, coercing types and dropping unmapped fields.
- **Detect drift** when a later ingestion renames, retypes, adds, or removes fields.

Everything is typed (Pydantic v2), tested, and runs offline.

---

## Install

```bash
# From PyPI
pip install canoniq

# From source (for development, or to run the bundled demos)
git clone https://github.com/Buchiexplores/canoniq.git
cd canoniq
pip install -e .
```

> The bundled `demo` datasets ship **inside the package**, so `canoniq demo <domain>`
> works straight from a `pip install` — no clone required.

### Optional extras

CanonIQ keeps the core dependency footprint small. Enterprise connectors are currently
**placeholders** (they raise a clear `NotImplementedError` naming the target version and required
extra) but the dependency groups are wired so future releases install cleanly.

| Extra | Install | Adds |
|---|---|---|
| `files` | `pip install "canoniq[files]"` | Parquet, Excel readers (planned) |
| `databases` | `pip install "canoniq[databases]"` | Postgres, MySQL, SQLite (planned) |
| `bigquery` | `pip install "canoniq[bigquery]"` | BigQuery (planned) |
| `snowflake` | `pip install "canoniq[snowflake]"` | Snowflake (planned) |
| `aws` | `pip install "canoniq[aws]"` | S3, Redshift (planned) |
| `gcp` | `pip install "canoniq[gcp]"` | GCS, BigQuery (planned) |
| `azure` | `pip install "canoniq[azure]"` | Azure Blob (planned) |
| `ai` | `pip install "canoniq[ai]"` | Local semantic matching adapter (sentence-transformers, off by default) |
| `all` | `pip install "canoniq[all]"` | Everything above |
| `dev` | `pip install "canoniq[dev]"` | pytest, mypy, ruff, coverage |

---

## Quickstart (CLI)

```bash
# Run the full pipeline end-to-end against a bundled example
canoniq demo higher-ed
canoniq demo retail
canoniq demo healthcare
canoniq demo finance
canoniq demo logistics

# Profile a file directly...
canoniq profile --source examples/higher_ed/source_students.csv --out profile.json

# ...or via a source-config (secrets resolved from ${ENV})
canoniq profile --source-config examples/sources/local_csv_students.yml --out profile.json

# Suggest → rules → apply → drift
canoniq suggest    --profile profile.json --canonical examples/higher_ed/canonical_student.yml --out suggestions.json
canoniq rules      --suggestions suggestions.json --canonical examples/higher_ed/canonical_student.yml --out rules.yml
canoniq apply      --source examples/higher_ed/source_students.csv --mapping suggestions.json \
                   --canonical examples/higher_ed/canonical_student.yml --out canonical.csv --include-review
canoniq drift-check --source examples/higher_ed/new_source_students.csv --mapping suggestions.json \
                   --canonical examples/higher_ed/canonical_student.yml --out drift.json

# Auto-onboard a provider (config-driven) and score deployment readiness
canoniq onboard       --config examples/retail_vendor_onboarding/onboarding_configs/brightmart_distribution.yml
canoniq onboard-batch --config-dir examples/retail_vendor_onboarding/onboarding_configs \
                   --combined-out examples/retail_vendor_onboarding/output/combined_readiness.json
```

## Auto-onboarding (config-driven)

Beyond the per-file pipeline, CanonIQ can **auto-onboard whole providers** from a
YAML config: profile every source, map it onto your canonical models, validate,
drift-check, and emit a single **deployment-readiness score** with a clear next
action — no deployment happens, you get a verdict plus the canonical artifacts.

A *provider* is whatever supplies data in your domain (a school, a vendor, a
hospital, a SaaS tenant). Two complete examples ship — same engine, different
industry: [higher education](examples/higher_ed_auto_onboarding/README.md) and
[retail vendors](examples/retail_vendor_onboarding/README.md).

```python
from canoniq.onboarding import onboard_provider

report = onboard_provider("path/to/provider.yml")
if report.auto_deploy_allowed:
    deploy(report)            # your deploy step
else:
    notify_reviewer(report)   # route to a human; see report.next_action
```

See the domain-neutral **[Auto-Onboarding Guide](docs/onboarding.md)** to build a
pipeline for any field.

## Quickstart (SDK)

```python
from canoniq import CanonIQ

engine = CanonIQ()  # local-first defaults

profile = engine.profile_source("examples/retail/source_products.csv")
mapping = engine.suggest_mappings(profile, "examples/retail/canonical_product.yml")

for m in mapping.mappings:
    print(f"{m.source_field:>16} -> {m.canonical_field or '(none)':<16} "
          f"{m.confidence:.2f} {m.status}  {', '.join(m.reasons)}")

rules = engine.generate_validation_rules(mapping, "examples/retail/canonical_product.yml", profile)
result = engine.apply_mapping(
    "examples/retail/source_products.csv", mapping,
    "examples/retail/canonical_product.yml", include_review=True,
)
report = engine.detect_drift(
    "examples/retail/new_source_products.csv", mapping,
    "examples/retail/canonical_product.yml",
)
print(report.status)  # "ok" or "drift_detected"
```

---

## Configuration

Every tunable lives in one YAML file — thresholds, scoring weights, sampling, PII
masking, and the optional AI adapter. Pass it to any CLI command with `--config`, or
load it in the SDK. Nothing is required; unspecified keys fall back to local-first
defaults. A fully commented example lives at
[`examples/config/canoniq.yml`](examples/config/canoniq.yml).

```bash
canoniq demo retail --config examples/config/canoniq.yml
canoniq suggest --profile profile.json --canonical canonical.yml --config examples/config/canoniq.yml
```

```python
from canoniq import CanonIQ
from canoniq.config import CanonIQConfig

engine = CanonIQ(CanonIQConfig.from_yaml("examples/config/canoniq.yml"))
```

### What AI model powers the mapping?

**By default, none — and that's intentional.** Core matching is a *deterministic*
ensemble of five signals (alias, name, type, pattern, range) with weighted, explained
confidence scores. It runs fully offline with zero network calls — the local-first
guarantee.

An **optional** sixth "semantic" signal is pluggable and **off by default**. Choose a
provider declaratively — no code. Three embedding backends ship today:

| Provider | Runs | Egress | Default model | API key |
|---|---|---|---|---|
| `sentence-transformers` (aliases `sbert`, `local`) | locally, on-device | **none** | `all-MiniLM-L6-v2` | — |
| `openai` | OpenAI API | field names only | `text-embedding-3-small` | `OPENAI_API_KEY` |
| `gemini` (aliases `google`) | Gemini API | field names only | `text-embedding-004` | `GEMINI_API_KEY` |

```yaml
# canoniq.yml — local, zero egress
ai:
  provider: sentence-transformers
  model: all-MiniLM-L6-v2     # any model version; omit to use the provider default
  weight: 0.15                # semantic contribution (auto-applied when enabled)
```

```yaml
# canoniq.yml — hosted (opt-in; sends field names to the provider)
ai:
  provider: openai            # or: gemini
  model: text-embedding-3-large
  api_key_env: OPENAI_API_KEY # env var name only — keys are never stored in config
  weight: 0.15
```

```bash
# local adapter needs the extra; hosted adapters need only an API key (stdlib HTTP)
pip install "canoniq[ai]"   # only for sentence-transformers
export OPENAI_API_KEY=sk-...
canoniq suggest --profile profile.json --canonical canonical.yml --config canoniq.yml
```

**Privacy guarantees for hosted providers:** only source field *names* and canonical
schema text are sent — **never sample values** (so masked PII/PHI never leaves). Keys
come from an environment variable, never the config file. Offline or missing key →
clear error; the deterministic pipeline always works without any adapter.

> **Anthropic / Claude** has no first-party text-embeddings API, so it can't power the
> embedding signal — configuring it fails fast with guidance. Claude is intended for a
> future optional *LLM reasoning* stage (resolving the `requires_review` band), not embeddings.

Plug in your own adapter (any provider, or a private model) by implementing
`BaseAIMatcher` and registering it:

```python
from canoniq.ai import BaseAIMatcher, register_ai_provider

class MyMatcher(BaseAIMatcher):
    def semantic_score(self, source_field, canonical_field) -> float:
        ...  # return a similarity in [0, 1]

register_ai_provider("my-matcher", lambda cfg: MyMatcher())
# then set ai.provider: my-matcher in your config
```

---

## Use cases

CanonIQ fits anywhere you repeatedly ingest external data into a trusted model:

- **Higher education** — map a new SIS/LMS export onto your OneRoster/Ed-Fi/CEDS student model.
- **Retail** — normalize supplier catalogs to a GS1 GTIN / schema.org product model.
- **Healthcare** — align partner feeds to an HL7 FHIR R4 `Patient` model with PHI masking.
- **Finance** — reconcile bank/payment files to an ISO 20022 transaction model with IBAN checks.
- **Logistics** — unify carrier feeds to a GS1 SSCC / SCAC shipment model.
- **SaaS onboarding** — turn every customer's CSV upload into your internal schema automatically.
- **AI agent platforms** — give an agent a deterministic, explainable tool for schema mapping.

See the per-domain walkthroughs in [`docs/`](docs/) and the **runnable sample use-cases** in
[`examples/`](examples/README.md) (`python examples/<domain>/demo.py`).

---

## Documentation

New here? Start with the **[Education & Onboarding Guide](docs/education/README.md)** — a
plain-English walkthrough of what CanonIQ is, why it's built this way, how to demo it, and
how to extend it.

| Doc | What it covers |
|---|---|
| [docs/education/](docs/education/README.md) | Plain-English guide: approach, architecture, onboarding, demos, use cases |
| [docs/quickstart.md](docs/quickstart.md) | Install, first pipeline, CLI + SDK |
| [docs/demos.md](docs/demos.md) | STAR walkthroughs of all 5 domain demos: the problem each solves + real output |
| [docs/onboarding.md](docs/onboarding.md) | Config-driven auto-onboarding: readiness scoring, build-your-own, enterprise adoption |
| [docs/concepts.md](docs/concepts.md) | Profiles, schemas, scoring, gating, drift |
| [docs/architecture.md](docs/architecture.md) | Module layout and data flow |
| [docs/connectors.md](docs/connectors.md) | How to add a connector |
| [docs/sources.md](docs/sources.md) | Source-config format, secrets, sampling |
| [docs/domain_packs.md](docs/domain_packs.md) | How to add a new domain |
| [docs/standards_mapping.md](docs/standards_mapping.md) | Canonical fields ↔ industry standards |
| [docs/roadmap.md](docs/roadmap.md) | Release plan |

Per-domain use cases:
[higher-ed](docs/higher_ed_use_case.md) ·
[retail](docs/retail_use_case.md) ·
[healthcare](docs/healthcare_use_case.md) ·
[finance](docs/finance_use_case.md) ·
[logistics](docs/logistics_use_case.md)

---

## Privacy & security

- Local-first: no source data, schemas, or mappings leave your machine in the core package.
- No telemetry in the MVP. No external API calls from the core.
- High-PII/PHI sample values are masked by default before they leave the profiler.
- All bundled example data is **synthetic**. No secrets live in the repo — source configs reference
  `${ENV}` variables only.

Report vulnerabilities per [SECURITY.md](SECURITY.md).

---

## Development

```bash
pip install -e ".[dev]"
pytest --cov=canoniq --cov-report=term-missing   # ≥80% coverage, zero network calls
ruff check canoniq
mypy canoniq
```

See [CONTRIBUTING.md](CONTRIBUTING.md) and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## License

[Apache-2.0](LICENSE) © The CanonIQ contributors.
