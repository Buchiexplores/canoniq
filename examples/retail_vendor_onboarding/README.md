# ShelfSync — Auto-Onboarding for Retail Vendors

A complete, runnable example of using **CanonIQ** to *auto-onboard* multiple data
providers — here, **retail vendors/suppliers** — by mapping each vendor's messy
product/inventory/order exports into shared canonical models, validating them,
checking for drift, and scoring how **deployment-ready** each provider is.

> **The pitch.** ShelfSync is a (fictional) marketplace + ERP integration layer.
> Every new vendor arrives with its own column names, file shapes, and quirks:
> one calls it `sku`, the next `product_sku`, a third `itm`. Instead of an
> engineer hand-writing a bespoke integration per vendor, ShelfSync points CanonIQ
> at each vendor's exports and gets back a **readiness score** and a **deployment
> recommendation** — *automatically*. Clean vendors flow straight through; messy
> ones are flagged with exactly what a human needs to fix. This is how you onboard
> the 500th supplier as easily as the 1st.

This is the **same provider-neutral pipeline** the higher-education example uses —
proof that CanonIQ is domain-agnostic. A "provider" is whatever supplies data in
your world; swap the canonical models and you have a different industry.

CanonIQ never deploys anything. It produces a *readiness verdict* plus the
canonical artifacts (mappings, validation rules, transformed records) that a
downstream deploy step could consume. The decision to ship stays with you.

---

## What this example demonstrates

For each vendor, CanonIQ runs the full pipeline per source:

```
load config → profile → suggest mappings → auto-approve high-confidence
→ flag the rest for review → generate validation rules → transform
→ drift-check (optional) → score readiness → recommend a next action
```

Three vendors are included to show the full spectrum of outcomes:

| Vendor | Profile | Outcome |
|---|---|---|
| **BrightMart Distribution** | Clean, canonical-aligned exports; complete data; stable catalog | Ready for auto-deploy |
| **Coastal Goods Co** | Solid data, but the sales export is missing the required `ordered_at` and a couple of columns don't map | Ready with minor review |
| **Anvil Hardware Supply** | Cryptic headers (`itm`, `grp`, `n`, `dt`), **no price or product name**, and a "next batch" that has already drifted | Blocked |

---

## Folder layout

```
retail_vendor_onboarding/
├── README.md                     # you are here
├── demo_auto_onboard.py          # runs all three vendors end-to-end
├── onboarding_configs/           # one YAML per vendor (the onboarding "plan")
│   ├── brightmart_distribution.yml
│   ├── coastal_goods.yml
│   └── anvil_hardware.yml
├── canonical/                    # the shared canonical models every vendor maps into
│   ├── canonical_product.yml
│   ├── canonical_inventory.yml
│   └── canonical_order.yml
├── vendors/                      # each vendor's raw, messy source exports (synthetic)
│   ├── brightmart_distribution/
│   │   ├── product_catalog.csv
│   │   ├── inventory_feed.csv
│   │   ├── sales_orders.csv
│   │   └── product_catalog_drift.csv   # a later batch, for drift detection
│   ├── coastal_goods/  ...
│   └── anvil_hardware/  ...
└── output/                       # generated readiness reports land here (git-ignored)
```

All data is **synthetic** — no real vendors, no real customers, no real PII.

---

## Run it

From the repository root, after `pip install -e .`:

```bash
# Option A — the demo script (writes per-vendor + combined reports to output/)
python examples/retail_vendor_onboarding/demo_auto_onboard.py

# Option B — the CLI, one vendor at a time
canoniq onboard \
  --config examples/retail_vendor_onboarding/onboarding_configs/brightmart_distribution.yml

# Option C — the CLI, every vendor in the directory + a combined roll-up
canoniq onboard-batch \
  --config-dir examples/retail_vendor_onboarding/onboarding_configs \
  --combined-out examples/retail_vendor_onboarding/output/combined_readiness.json
```

---

## Results (from the bundled synthetic data)

```
┌──────────────────────────┬───────┬─────────────────────────┬─────────────┐
│ provider                 │ score │ status                  │ auto-deploy │
├──────────────────────────┼───────┼─────────────────────────┼─────────────┤
│ BrightMart Distribution  │    90 │ ready_for_auto_deploy   │ yes         │
│ Coastal Goods Co         │    82 │ ready_with_minor_review │ no          │
│ Anvil Hardware Supply    │    18 │ blocked                 │ no          │
└──────────────────────────┴───────┴─────────────────────────┴─────────────┘
  1 auto / 1 minor-review / 0 needs-review / 1 blocked  (3 total)
```

A few things worth noticing:

- **BrightMart scores 90 and is cleared for auto-deploy** — its columns are named
  exactly like the canonical fields, every required field is covered across its
  product/inventory/order feeds, validation passes, and its next catalog batch
  shows no drift.
- **Coastal scores 82** but auto-deploy is **withheld**: its `sales_orders.csv`
  has no order-timestamp column, so the order entity's required `ordered_at` is
  uncovered and `required_fields_covered = false`. The score is promising, but the
  policy gate correctly holds it for a human.
- **Anvil scores 18 and is blocked**: its catalog has cryptic headers and carries
  neither a price nor a product name, most columns don't map, required coverage is
  zero, and its next batch has already drifted (columns added and removed).
- Even on clean data, CanonIQ is **conservative about auto-approval** — most exact
  alias matches still land in `requires_review` rather than `auto_approved`. That's
  by design: auto-approval is reserved for the highest-confidence matches, and the
  readiness score rewards review-grade mappings while keeping a human in the loop.

---

## How the readiness score works

The score is a weighted blend of five components (weights sum to 1.0):

| Component | Weight | Ratio measured |
|---|---:|---|
| Schema mapping coverage | 35% | mapped source fields ÷ total source fields |
| Required field coverage | 25% | required canonical fields covered ÷ required total |
| Validation rule coverage | 15% | passing validation findings ÷ total findings |
| Auto-approved mapping ratio | 15% | auto-approved mappings ÷ mapped fields |
| Drift status | 10% | drift-checked sources with no drift ÷ checked sources |

`readiness_score = round(Σ ratioᵢ × weightᵢ × 100)`

**Status bands:**

| Score | Status |
|---|---|
| 90–100 | `ready_for_auto_deploy` |
| 80–89 | `ready_with_minor_review` |
| 60–79 | `needs_mapping_review` |
| below 60 | `blocked` |

**Required-field coverage is computed per entity, using the union of every source
that targets it.** A vendor's `product_catalog.csv` and `inventory_feed.csv` both
contribute to coverage of the entities they target; CanonIQ evaluates the entity,
not the individual file.

### When is auto-deploy allowed?

```
auto_deploy_allowed = (readiness_score >= minimum_readiness_score)
                      AND (all required fields are covered)
                      AND (no critical/error-severity validation failures)
```

`minimum_readiness_score` (default **90**) and the two `require_*` switches live in
each config's `deployment:` block, so a vendor can have its own gate.

---

## The onboarding config

Each vendor is described by one YAML file. Paths are resolved relative to the
config file, so configs and data travel together:

```yaml
provider:
  id: brightmart_distribution
  name: BrightMart Distribution
  environment: staging
deployment:
  minimum_readiness_score: 90
  require_required_fields: true
  require_validation_pass: true
sources:
  - name: product_catalog
    entity: product
    path: ../vendors/brightmart_distribution/product_catalog.csv
    canonical: ../canonical/canonical_product.yml
    drift_path: ../vendors/brightmart_distribution/product_catalog_drift.csv  # optional
  - name: inventory_feed
    entity: inventory
    path: ../vendors/brightmart_distribution/inventory_feed.csv
    canonical: ../canonical/canonical_inventory.yml
  - name: sales_orders
    entity: order
    path: ../vendors/brightmart_distribution/sales_orders.csv
    canonical: ../canonical/canonical_order.yml
output:
  dir: ../output/brightmart_distribution
```

A source maps **one file → one canonical entity**. Multiple sources may target the
same entity. Add `drift_path` to compare a later batch against the mapping CanonIQ
just learned.

---

## Example mappings CanonIQ discovers

A sample of the source→canonical mappings inferred from aliases, names, types, and
value patterns (no hand-written rules):

| Vendor source column | → Canonical field |
|---|---|
| `item_sku`, `product_sku`, `sku_code`, `item_number` | `product.sku` |
| `barcode`, `upc`, `ean` | `product.gtin` |
| `title`, `item_name`, `name` | `product.product_name` |
| `list_price`, `retail_price`, `price` | `product.unit_price` |
| `location_id`, `warehouse`, `dc_id` | `inventory.warehouse_id` |
| `qty_on_hand`, `stock_level`, `available_qty` | `inventory.quantity_on_hand` |
| `order_number`, `sales_order_id`, `po_number` | `order.order_id` |
| `order_date`, `placed_at`, `order_datetime` | `order.ordered_at` |
| `sales_channel`, `marketplace_channel` | `order.channel` |

---

## The readiness report

`onboard` writes one JSON report per vendor (shape abbreviated):

```json
{
  "provider_id": "brightmart_distribution",
  "provider_name": "BrightMart Distribution",
  "environment": "staging",
  "status": "ready_for_auto_deploy",
  "readiness_score": 90,
  "summary": {
    "total_fields": 17,
    "mapped_fields": 17,
    "auto_approved_mappings": 6,
    "requires_review": 11,
    "low_confidence": 0,
    "required_fields_covered": true
  },
  "component_scores": { "schema_mapping": { "ratio": 1.0, "weight": 0.35, "points": 35.0 }, "...": "..." },
  "sources": [ { "source": "product_catalog", "entity": "product", "drift_status": "no_drift", "...": "..." } ],
  "deployment_recommendation": "All required fields are mapped with high confidence ...",
  "auto_deploy_allowed": true,
  "next_action": "auto_deploy"
}
```

`onboard-batch` additionally writes a `combined_readiness.json` roll-up counting how
many providers landed in each status band.

---

## Where the code lives

The reusable logic is a first-class part of the library, not example-only glue:

- `canoniq/onboarding/config.py` — config models + loader
- `canoniq/onboarding/readiness.py` — scoring weights, status bands, `compute_readiness`
- `canoniq/onboarding/orchestrator.py` — `onboard_provider` / `onboard_providers`
- `canoniq/onboarding/models.py` — the report Pydantic models

so you can call it directly:

```python
from canoniq.onboarding import onboard_provider

report = onboard_provider("path/to/vendor.yml")
if report.auto_deploy_allowed:
    deploy(report)        # your code
else:
    notify_reviewer(report)
```

---

## Build your own domain

This example and the [higher-education example](../higher_ed_auto_onboarding/) share
the *exact same engine*. To onboard providers in **your** domain:

1. Write canonical schema YAMLs for your entities (see `canonical/`).
2. Drop each provider's source files somewhere and write one onboarding config per
   provider pointing at them.
3. Run `canoniq onboard-batch --config-dir <your_configs>`.

See [`docs/onboarding.md`](../../docs/onboarding.md) for the full, domain-neutral guide.
