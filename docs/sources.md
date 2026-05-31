# Source configs

A **source-config** is a small YAML file describing where data lives and how to sample it. It lets
you point CanonIQ at any registered connector without writing code, and keeps secrets out of the
repo by resolving them from environment variables.

```bash
canoniq profile --source-config examples/sources/local_csv_students.yml --out profile.json
```

## Format

```yaml
source:
  type: csv                 # registered connector type (see connectors.md)
  path: examples/higher_ed/source_students.csv
  sample_limit: 1000        # how many records to sample for profiling
```

Every config has a top-level `source:` mapping. The `type` selects the connector; the remaining
keys are passed through to that connector. `sample_limit` controls how many records the profiler
reads (falls back to the engine default when omitted). For multi-entity sources, set `entity:` to
choose the table/collection/file.

## Secrets via `${ENV}`

Credentials are **never** inlined. Use `${VAR}` placeholders; the loader interpolates them from the
environment at load time. If a value looks like a hard-coded secret, the loader logs a warning on
the `canoniq.sources` logger.

```yaml
# Requires the databases extra: pip install "canoniq[databases]"
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

```bash
export POSTGRES_HOST=... POSTGRES_PORT=5432 POSTGRES_DB=... \
       POSTGRES_USER=... POSTGRES_PASSWORD=...
canoniq profile --source-config sources/postgres_customers.yml --out profile.json
```

## Bundled examples

`examples/sources/` contains runnable and reference configs:

| File | Type | Notes |
|---|---|---|
| `local_csv_students.yml` | csv | Runs offline against bundled data. |
| `local_json_products.yml` | json | Runs offline against bundled data. |
| `postgres_customers.yml` | postgres | `${POSTGRES_*}`; needs `databases` extra (planned). |
| `bigquery_students.yml` | bigquery | `${GCP_PROJECT_ID}`, ADC; needs `bigquery` extra (planned). |
| `snowflake_transactions.yml` | snowflake | `${SNOWFLAKE_*}`; needs `snowflake` extra (planned). |
| `s3_orders.yml` | s3 | `${S3_BUCKET}`, `format: parquet`; needs `aws` extra (planned). |
| `gcs_lms_activity.yml` | gcs | `${GCS_BUCKET}`, `format: jsonl`; needs `gcp` extra (planned). |

The two `local_*` configs run today. The rest reference placeholder connectors: they load and build
a connector, but sampling raises a clear `NotImplementedError` naming the target version and extra
until that connector lands.

## Sampling strategy

Profiling reads up to `sample_limit` records. Larger samples give better type/range/enum inference
at the cost of time; the default balances both. Sampling is the only thing that reads source data,
and it never leaves your machine.
