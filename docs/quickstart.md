# Quickstart

CanonIQ maps a source dataset onto a canonical schema, end to end, on your machine.
This guide gets you from install to a full pipeline in a few minutes.

## Install

```bash
pip install canoniq           # core: CSV/JSON/JSONL + full pipeline + CLI
# or, from source:
git clone https://github.com/Buchiexplores/canoniq.git
cd canoniq && pip install -e .
```

For development tooling (pytest, ruff, mypy):

```bash
pip install -e ".[dev]"
```

## Run a bundled demo

The fastest way to see the whole pipeline is the `demo` command. It profiles a synthetic
source, suggests mappings, generates rules, transforms, and detects drift — writing all
outputs under `out/<entity>/`.

```bash
canoniq demo higher-ed
canoniq demo retail
canoniq demo healthcare
canoniq demo finance
canoniq demo logistics
```

Each run prints a suggestions table plus a summary (profiled fields, auto/review counts,
rule count, canonical rows, drift status, output dir).

## Step through the pipeline yourself

```bash
# 1. Profile (dispatches on extension: .csv/.json/.jsonl/.ndjson)
canoniq profile --source examples/higher_ed/source_students.csv --out profile.json

# 1b. ...or profile via a source-config (secrets come from ${ENV})
canoniq profile --source-config examples/sources/local_csv_students.yml --out profile.json

# 2. Suggest mappings against a canonical schema
canoniq suggest --profile profile.json \
  --canonical examples/higher_ed/canonical_student.yml --out suggestions.json

# 3. Generate validation rules
canoniq rules --suggestions suggestions.json \
  --canonical examples/higher_ed/canonical_student.yml --out rules.yml

# 4. Transform to canonical CSV (include review-tier mappings too)
canoniq apply --source examples/higher_ed/source_students.csv \
  --mapping suggestions.json --canonical examples/higher_ed/canonical_student.yml \
  --out canonical.csv --include-review

# 5. Detect drift against a later ingestion
canoniq drift-check --source examples/higher_ed/new_source_students.csv \
  --mapping suggestions.json --canonical examples/higher_ed/canonical_student.yml \
  --out drift.json
```

## Same pipeline via the SDK

```python
from canoniq import CanonIQ

engine = CanonIQ()
profile = engine.profile_source("examples/finance/source_transactions.csv")
mapping = engine.suggest_mappings(profile, "examples/finance/canonical_transaction.yml")
rules   = engine.generate_validation_rules(mapping, "examples/finance/canonical_transaction.yml", profile)
result  = engine.apply_mapping(
    "examples/finance/source_transactions.csv", mapping,
    "examples/finance/canonical_transaction.yml", include_review=True,
)
report  = engine.detect_drift(
    "examples/finance/new_source_transactions.csv", mapping,
    "examples/finance/canonical_transaction.yml",
)
print(report.status)
```

## Tuning behavior

Construct a `CanonIQConfig` to change thresholds, scoring weights, or sampling:

```python
from canoniq import CanonIQ
from canoniq.config import CanonIQConfig

cfg = CanonIQConfig(auto_approve_threshold=0.95, mask_pii=True, sample_limit=5000)
engine = CanonIQ(config=cfg)
```

Config can also be loaded from YAML with `CanonIQConfig.from_yaml("canoniq.yml")` and
overridden field-by-field with `cfg.with_overrides(review_threshold=0.6)`.

Next: [concepts.md](concepts.md) explains profiles, schemas, scoring, gating, and drift.
