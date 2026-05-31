# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Configurable AI adapter layer: an `ai:` config block (provider, model, api_key_env,
  weight, options), a provider registry/factory (`register_ai_provider`,
  `build_ai_matcher`), and a bundled local `sentence-transformers` adapter (default
  `all-MiniLM-L6-v2`, off by default, requires the `[ai]` extra). Enabling a model is
  now a one-line YAML change — no code — and CanonIQ auto-enables the semantic weight
  when an adapter is on.
- Optional hosted embedding adapters for the semantic signal: `openai`
  (default `text-embedding-3-small`) and `gemini`/`google`
  (default `text-embedding-004`), implemented on the Python standard library
  (`urllib`) with **zero new dependencies**. Provider and model version are selected
  declaratively in config; API keys come from an environment variable named by
  `api_key_env` (never stored in config). Hosted providers send source field *names*
  and canonical schema text only — never sample values, so masked PII/PHI never leaves.
  Per-text embedding caching minimizes API calls.
- `anthropic`/`claude` providers are registered but fail fast with an actionable error:
  Claude has no first-party text-embeddings API, so it cannot power the embedding
  signal (it is reserved for a future optional LLM reasoning stage).
- `--config` option on all CLI commands to load thresholds, scoring weights, sampling,
  PII masking, and the AI adapter from a single YAML file.
- Commented example config at `examples/config/canoniq.yml`.

## [0.1.0] - 2026-05-29

### Added

- Domain-agnostic, source-agnostic canonical mapping engine (`CanonIQ` SDK facade).
- Typer + Rich CLI: `version`, `profile`, `suggest`, `rules`, `apply`,
  `drift-check`, `demo`.
- Real connectors: CSV, JSON, JSONL/NDJSON.
- Placeholder connectors for Parquet, Excel, SQLite, Postgres, MySQL, BigQuery,
  Snowflake, Redshift, S3, GCS, Azure Blob, and REST API; each raises a clear
  `NotImplementedError` naming its target version and required extra.
- Source-config YAML loader with `${ENV}` interpolation and inline-secret warnings.
- Source-agnostic profiler: type inference, pattern detection, and PII/PHI
  detection with masking on by default.
- Canonical-schema YAML loader supporting production-grade field metadata
  (standards, format, pii, unit, enum).
- Matchers (alias, name, type, pattern, range), mapping engine, and weighted
  confidence scoring with configurable weights and thresholds.
- Validation-rule generation and format validators with checksums (IBAN, GTIN,
  NPI, LEI) plus primitive validators (ISO 8601, ISO 3166, ISO 4217, email, UUID).
- Transformation to canonical records with type coercion and unmapped-field drop.
- Drift detection across ingestions (missing, new, type-change, unmapped-required,
  suggested remappings).
- Five bundled domain examples with synthetic data and drift variants:
  higher education, retail, healthcare, finance, logistics.
- Optional AI adapter interface with a no-op default (off by default).
- Test suite with golden-file determinism checks and network isolation; coverage
  gate at 80%.
- Documentation set, CI workflow, and Docker image.
- Runnable `demo.py` for every domain plus an `examples/` catalog of sample use-cases.
- GitHub community-health files: issue forms, pull-request template, CODEOWNERS, and
  Dependabot configuration.

### Security

- Local-first: no source data, schemas, or mappings leave the machine in the core.
- No telemetry; no external network calls in the core package.
- Synthetic example data only; no secrets in the repository.

[Unreleased]: https://github.com/okyke-technologies/canoniq/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/okyke-technologies/canoniq/releases/tag/v0.1.0
