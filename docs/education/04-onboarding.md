# 04 — Onboarding

Two tracks: **users** (I just want to run it) and **developers** (I want to extend it).

---

## Track A — Users (5 minutes)

### 1. Install

```bash
pip install canoniq          # or, from a clone: pip install -e .
```

### 2. See the whole thing work

```bash
canoniq demo higher-ed
```

This runs profile → suggest → rules → apply → drift on bundled synthetic data and prints
a summary table. Try `retail`, `healthcare`, `finance`, `logistics` too.

### 3. Run it on a file (the 5 core commands)

```bash
# Describe a file
canoniq profile --source mydata.csv --out profile.json

# Suggest mappings to your model
canoniq suggest --profile profile.json --canonical mymodel.yml --out suggestions.json

# Generate validation rules
canoniq rules --suggestions suggestions.json --canonical mymodel.yml --out rules.yml

# Produce clean canonical output
canoniq apply --source mydata.csv --mapping suggestions.json \
  --canonical mymodel.yml --out clean.csv --include-review

# Check a later file for drift
canoniq drift-check --source newdata.csv --mapping suggestions.json \
  --canonical mymodel.yml --out drift.json
```

### 4. Write your own canonical model

A canonical model is a YAML file. The most important key is **`aliases`** — the more
real-world column names you list, the better the auto-mapping:

```yaml
domain: my_company
entity: customer
version: 1
primary_key: [customer_id]
fields:
  customer_id:
    type: string
    required: true
    aliases: [cust_id, client_id, customer_no, id]
  email:
    type: email
    required: true
    format: email
    pii: moderate
    aliases: [email_address, contact_email, e_mail]
```

That's it — point `--canonical` at it and you're mapping your own model.

---

## Track B — Developers

### 1. Set up

```bash
git clone https://github.com/Buchiexplores/canoniq.git
cd canoniq
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. The three checks (CI runs the same ones)

```bash
ruff check canoniq tests            # style/lint
mypy canoniq                        # type-check
pytest --cov=canoniq --cov-report=term-missing   # tests, 80%+ coverage, zero network
```

### 3. Where things live (map of the codebase)

```
canoniq/
  engine.py        ← the SDK facade (start reading here)
  cli.py           ← the terminal commands
  config.py        ← thresholds, weights, sampling
  core/models.py   ← the typed data shapes
  connectors/      ← read data sources (CSV/JSON/JSONL real; rest are stubs)
  profiler/        ← type/pattern/PII detection
  matcher/         ← the 5 matchers + the mapping engine
  scoring/         ← weighted confidence
  validation/      ← rule generation + format checksums
  transform/       ← reshape to canonical
  drift/           ← compare a new file to a saved mapping
  domains/         ← the 5 bundled examples (data only)
```

A good first read order: `engine.py` → `core/models.py` → `matcher/mapping_engine.py`.

### 4. Common extension tasks

| I want to… | Do this | Guide |
|---|---|---|
| Support a new data source | Add a connector class, register it | [docs/connectors.md](../connectors.md) |
| Add a new industry/model | Add a YAML schema + synthetic data | [docs/domain_packs.md](../domain_packs.md) |
| Point at a database/cloud source | Write a source-config YAML | [docs/sources.md](../sources.md) |
| Change how aggressive auto-mapping is | Tune `CanonIQConfig` thresholds/weights | [docs/concepts.md](../concepts.md) |

### 5. The rules every contribution must follow

- **No network calls** in the core or in tests (a socket guard enforces this).
- **Synthetic data only** — never commit real personal/health/financial/education data.
- **No secrets** — source configs use `${ENV}` placeholders only.
- **Tests + 80% coverage** for new code.

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for the full checklist.

Next: **[05 — Use cases (with examples)](05-use-cases.md)**
