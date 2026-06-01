# Auto-Onboarding Guide

CanonIQ's **auto-onboarding** workflow takes one or more *providers* — each with
its own messy source files — profiles every source, maps it onto your shared
canonical models, validates and (optionally) drift-checks it, and produces a single
**deployment-readiness score** plus a clear next action. It never deploys anything;
the output is a *verdict* and the canonical artifacts a deploy step could consume.

> **"Provider" is deliberately generic.** A provider is whatever supplies data in
> your domain: a school, a retail vendor, a hospital, a SaaS tenant, a partner
> bank, a franchise location, a data broker. The engine is identical across all of
> them — only the canonical schemas and the source files change. Two fully worked
> examples ship in [`examples/`](../examples): higher education and retail vendors.

---

## When to use it

Reach for auto-onboarding when you repeatedly integrate **the same shape of data
from many different sources**, and you want a consistent, automatable gate before
anything reaches production:

- Onboarding the 1st vs the 500th supplier/tenant/partner should cost the same.
- You want a machine-checkable answer to *"is this source clean enough to ship?"*
- You want messy sources flagged with **exactly what a human must fix**, not a
  vague failure.

If you only need a one-off profile/map/validate of a single file, the lower-level
SDK (`CanonIQ.profile_source`, `suggest_mappings`, `validate`) is enough. Auto-
onboarding is the orchestration layer that runs that pipeline per source, rolls it
up per provider, and scores the result.

---

## The pipeline

```
per source:    profile → suggest mappings → generate validation rules
               → transform → (optional) drift-check
per provider:  aggregate the source outcomes → weighted readiness score
               → status band → deployment recommendation → next action
```

Everything is **deterministic** given the same inputs and config, and **local-first**
— no source data leaves your machine, no telemetry, no network calls.

---

## Quick start

After `pip install -e .` (see the [quickstart](quickstart.md)):

```bash
# One provider
canoniq onboard --config path/to/provider.yml

# Every provider in a directory, with a combined roll-up
canoniq onboard-batch \
  --config-dir path/to/configs \
  --combined-out path/to/output/combined_readiness.json
```

Or from Python:

```python
from canoniq.onboarding import onboard_provider, onboard_providers

report = onboard_provider("path/to/provider.yml")
if report.auto_deploy_allowed:
    deploy(report)          # your deploy step
else:
    notify_reviewer(report) # route to a human with report.next_action

# Batch:
reports, combined = onboard_providers("path/to/configs")
print(combined.ready_for_auto_deploy, "of", combined.total_providers, "ready")
```

Try it immediately against a bundled example:

```bash
python examples/retail_vendor_onboarding/demo_auto_onboard.py
python examples/higher_ed_auto_onboarding/demo_auto_onboard.py
```

---

## The onboarding config

One YAML file describes **one provider**. Every path is resolved **relative to the
config file's directory**, so configs and data travel together.

```yaml
provider:
  id: acme_supplier            # stable id; used in output filenames
  name: ACME Supplier Inc.     # human-readable label
  environment: staging         # free-form: staging / prod / sandbox / ...
deployment:
  minimum_readiness_score: 90  # auto-deploy gate (default 90)
  require_required_fields: true
  require_validation_pass: true
sources:
  - name: product_catalog      # logical name for this feed
    entity: product            # which canonical entity it maps to
    path: ../data/acme/catalog.csv
    canonical: ../canonical/canonical_product.yml
    drift_path: ../data/acme/catalog_next_batch.csv   # optional drift check
  - name: inventory_feed
    entity: inventory
    path: ../data/acme/inventory.csv
    canonical: ../canonical/canonical_inventory.yml
output:
  dir: ../output/acme_supplier # where the readiness report is written
```

Notes:

- A source maps **one file → one canonical entity**. Multiple sources may target
  the same entity (e.g. two feeds both contribute to `product`); coverage is
  evaluated on the **union** of those sources.
- `drift_path` is optional. When present, CanonIQ compares that "next batch"
  against the mapping it just learned and reports whether the schema drifted.
- Supported source formats follow the connector layer (CSV, JSON, JSONL, and the
  optional extras). See [connectors.md](connectors.md).

### Config reference

| Field | Required | Default | Meaning |
|---|---|---|---|
| `provider.id` | yes | — | Stable identifier; used in `{id}_readiness.json` |
| `provider.name` | yes | — | Human-readable provider name |
| `provider.environment` | no | `staging` | Free-form target environment label |
| `deployment.minimum_readiness_score` | no | `90` | Score gate for auto-deploy |
| `deployment.require_required_fields` | no | `true` | Block auto-deploy unless all required fields covered |
| `deployment.require_validation_pass` | no | `true` | Block auto-deploy on error-severity validation failures |
| `sources[].name` | yes | — | Logical feed name |
| `sources[].entity` | yes | — | Canonical entity this feed maps to |
| `sources[].path` | yes | — | Source data file (resolved relative to config) |
| `sources[].canonical` | yes | — | Canonical schema YAML (resolved relative to config) |
| `sources[].drift_path` | no | — | Optional later batch for drift detection |
| `output.dir` | no | — | Directory for the readiness report (omit to skip writing) |

---

## The canonical schema

Canonical schemas are ordinary CanonIQ entity YAMLs — the same ones the rest of the
library uses. Each declares fields with types, requiredness, aliases, and optional
constraints/standards. Aliases are what let the matcher recognize a provider's
column names without hand-written rules.

```yaml
domain: retail
entity: product
version: 1
primary_key: [sku]
fields:
  sku:
    type: string
    required: true
    aliases: [item_sku, product_sku, sku_code, item_number, product_id]
  product_name:
    type: string
    required: true
    aliases: [name, title, item_name, product_title]
  unit_price:
    type: decimal
    required: true
    min: 0.0
    aliases: [price, list_price, retail_price, sell_price]
```

See [concepts.md](concepts.md) and [standards_mapping.md](standards_mapping.md) for
the full field grammar and standards mapping.

---

## The readiness score

The score is a weighted blend of five components (weights sum to 1.0):

| Component | Weight | Ratio measured |
|---|---:|---|
| `schema_mapping` | 35% | mapped source fields ÷ total source fields |
| `required_fields` | 25% | required canonical fields covered ÷ required total |
| `validation` | 15% | passing validation findings ÷ total findings |
| `auto_approved` | 15% | auto-approved mappings ÷ mapped fields |
| `drift` | 10% | drift-checked sources with no drift ÷ checked sources |

```
readiness_score = round(Σ ratioᵢ × weightᵢ × 100)
```

**Status bands:**

| Score | Status | Next action |
|---|---|---|
| 90–100 | `ready_for_auto_deploy` | `auto_deploy` |
| 80–89 | `ready_with_minor_review` | `review_then_deploy` |
| 60–79 | `needs_mapping_review` | `resolve_mappings` |
| below 60 | `blocked` | `block_and_escalate` |

**Required-field coverage is computed per entity, using the union of every source
that targets it.** A single feed need not carry every required field; CanonIQ
evaluates the entity across all of its sources.

**A field counts as "mapped" only at review-grade confidence or above.** CanonIQ is
deliberately conservative: a bare alias match (no corroborating type/pattern/range
signal) often lands in `low_confidence` and does *not* count toward mapping
coverage. Auto-approval is reserved for the highest-confidence matches. See
[concepts.md](concepts.md) for the matcher's signal weights and thresholds.

### When is auto-deploy allowed?

```
auto_deploy_allowed = (readiness_score >= minimum_readiness_score)
                      AND (require_required_fields ⇒ all required fields covered)
                      AND (require_validation_pass ⇒ no error-severity validation failures)
```

The gate is per-provider: each config's `deployment:` block can tighten or relax it.

---

## The readiness report

`onboard` writes one `{provider_id}_readiness.json` per provider:

```json
{
  "provider_id": "acme_supplier",
  "provider_name": "ACME Supplier Inc.",
  "environment": "staging",
  "status": "ready_for_auto_deploy",
  "readiness_score": 90,
  "summary": {
    "total_fields": 17, "mapped_fields": 17, "auto_approved_mappings": 6,
    "requires_review": 11, "low_confidence": 0, "required_fields_covered": true
  },
  "component_scores": { "schema_mapping": { "ratio": 1.0, "weight": 0.35, "points": 35.0 } },
  "sources": [ { "source": "product_catalog", "entity": "product", "drift_status": "no_drift" } ],
  "deployment_recommendation": "All required fields are mapped ...",
  "auto_deploy_allowed": true,
  "next_action": "auto_deploy"
}
```

`onboard-batch` additionally writes a `combined_readiness.json` roll-up with
per-provider headline entries and counts per status band.

---

## Build your own domain in four steps

1. **Model your entities.** Write a canonical schema YAML per entity, with generous
   `aliases` for the column names your providers actually use.
2. **Point at your data.** For each provider, write one onboarding config listing
   its source files and the entity each maps to.
3. **Run it.** `canoniq onboard-batch --config-dir <your_configs>` (or call
   `onboard_providers` from Python).
4. **Wire the verdict in.** Branch on `report.auto_deploy_allowed` /
   `report.next_action`: auto-promote the ready ones, route the rest to reviewers.

Copy either bundled example as a starting skeleton — they share the exact same
engine, so whichever is closer to your domain is a valid template.

---

## Enterprise adoption & scalability

CanonIQ is designed to drop into existing data platforms without lock-in:

- **Local-first & private.** No source data, schemas, or sample values are sent to
  any external service. There is no telemetry and tests make zero network calls —
  safe for regulated environments (PII/PHI, finance, healthcare).
- **Deterministic & auditable.** The same inputs always produce the same score.
  Every readiness report is a self-contained JSON artifact you can archive, diff,
  and attach to an audit trail or change request.
- **Stateless & parallelizable.** Each provider onboarding is independent. Run
  thousands of configs across CI workers or a job queue; there is no shared mutable
  state. `onboard_providers` simply iterates, so you can shard a config directory
  across machines and merge the combined reports.
- **CI/CD-native.** Wire `canoniq onboard-batch` into a pipeline step: fail the
  build (or open a review ticket) for any provider below your gate, auto-promote the
  rest. Reports are machine-readable for dashboards and alerting.
- **Policy per provider.** The `deployment:` block lets different providers (or
  different environments) carry different gates — strict for production, looser for
  sandbox.
- **Typed & versioned.** Models are Pydantic v2 with `extra="forbid"`; every report
  records the `canoniq_version` that produced it, so you can detect scoring changes
  across upgrades.
- **Extensible connectors.** Add new source backends (databases, object stores,
  APIs) behind the connector interface without touching the onboarding logic. See
  [connectors.md](connectors.md).

### Suggested rollout

1. Pilot with a handful of representative providers; tune canonical aliases until
   clean sources reach `ready_for_auto_deploy`.
2. Add `onboard-batch` to CI as a **non-blocking** report to build confidence.
3. Flip it to **blocking** at your chosen `minimum_readiness_score`, with a review
   queue fed by `needs_mapping_review` / `ready_with_minor_review`.
4. Automate promotion of `auto_deploy_allowed` providers into your deploy step.

---

## See also

- [examples/higher_ed_auto_onboarding](../examples/higher_ed_auto_onboarding) — worked higher-education example
- [examples/retail_vendor_onboarding](../examples/retail_vendor_onboarding) — worked retail-vendor example
- [concepts.md](concepts.md) — matcher signals, confidence, validation
- [connectors.md](connectors.md) — source format support
- [architecture.md](architecture.md) — how the pieces fit together
