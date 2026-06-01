# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **[Privacy & Security guide](docs/security.md)** documenting local-first design,
  PII/PHI detection + default masking (with exact behavior), the optional AI adapter's
  data-egress guarantees (field names + schema only — never data values), secret
  handling via `${ENV}`, determinism/auditability, and regulated-industry
  (HIPAA / GDPR / PCI / SOC 2) adoption guidance. Linked from the README and SECURITY.md.

## [0.3.1] - 2026-06-01

### Changed

- **Every `canoniq demo <domain>` is now a comprehensive, narrated walkthrough.** The
  `retail`, `healthcare`, `finance`, and `logistics` demos now show — like `higher-ed`
  — the use-case framing, the pipeline, field-level mappings *with the reason for each
  decision*, the generated validation rules and their findings, the transform result
  (with a sample row), detailed drift (missing / new / suggested remappings), and a
  "why it matters" takeaway. Backed by a new packaged renderer
  (`canoniq.demos.run_pipeline_demo`).

## [0.3.0] - 2026-06-01

### Added

- **`canoniq demo higher-ed` is now a comprehensive, multi-school auto-onboarding
  walkthrough** (CampusLaunch AI), shipped in the package so it works from a plain
  `pip install`. It narrates the use case and pipeline, then for each of three
  schools shows the messy→canonical field mappings *with the reason for every
  decision*, a per-source breakdown, the readiness-score math, and the verdict —
  ending with a portfolio roll-up and an illustrative ROI summary. The other domains
  (`retail`, `healthcare`, `finance`, `logistics`) keep the quick single-source demo.
- New packaged module `canoniq.demos` (`run_campuslaunch_demo`) and bundled
  onboarding data (`canoniq/demo_data/higher_ed_onboarding/`); the repo's
  `examples/higher_ed_auto_onboarding/demo_auto_onboard.py` is now a thin wrapper
  over it (single source of truth).
- Sync-guard test ensuring the packaged onboarding data matches the repo example.

### Changed

- The higher-education example README gains a schema-variance table and a Business
  value / ROI section.

## [0.2.2] - 2026-06-01

### Fixed

- `canoniq demo <domain>` now works from a plain `pip install` — the demo datasets
  are **bundled inside the package** (`canoniq/demo_data/`) instead of relying on the
  repo's `examples/` tree (which isn't shipped in the wheel). Previously, running a
  demo from an installed package raised a `FileNotFoundError`.
- The `demo` command now exits cleanly with an actionable message (no traceback) if
  the bundled data is ever missing.

### Added

- Sync-guard test ensuring the packaged demo data stays byte-for-byte identical to
  the repo `examples/` copies.

## [0.2.1] - 2026-06-01

### Added

- `canoniq demo` now frames each run as a **STAR use case** — a Situation/Task/Action
  panel before the pipeline and a "Why it matters" Result panel after — so the demo
  explains the real-world problem it solves, not just the mapping table. Full
  write-ups live in [docs/demos.md](docs/demos.md).

## [0.2.0] - 2026-06-01

First public release on PyPI (`pip install canoniq`).

### Added

- **Config-driven auto-onboarding** (`canoniq.onboarding`): profile → map → validate →
  drift-check every source of a *provider*, then roll the outcomes into a single 0–100
  **deployment-readiness score** with status bands, a deployment recommendation, and a
  next action. New CLI commands `canoniq onboard` (one provider) and
  `canoniq onboard-batch` (a directory of providers + combined roll-up); new SDK
  entrypoints `onboard_provider` / `onboard_providers`. The API is **provider-neutral**
  so it fits any domain (school, retail vendor, hospital, SaaS tenant, …).
- Two complete, runnable onboarding examples sharing the exact same engine:
  `examples/higher_ed_auto_onboarding/` (CampusLaunch AI — universities) and
  `examples/retail_vendor_onboarding/` (ShelfSync — retail vendors). Each spans the
  full outcome spectrum (auto-deploy / minor-review / blocked) on synthetic data.
- Domain-neutral [Auto-Onboarding Guide](docs/onboarding.md): config reference,
  scoring model, build-your-own-pipeline steps, and enterprise adoption/scalability
  guidance.
- Stakeholder pipeline visualizations (Mermaid) in the higher-education case study.
- Automated PyPI release workflow (`.github/workflows/release.yml`) using OIDC
  Trusted Publishing — tag `vX.Y.Z` to build, verify, and publish; the workflow
  fails if the tag does not match the `pyproject.toml` version.
- `canoniq.core` now re-exports the public Pydantic data types (`MappingResult`,
  `ValidationReport`, `DriftReport`, profiles, …) for a cleaner SDK import surface.
- `canoniq.domains.examples_available()` helper.

### Changed

- Onboarding API is provider-neutral: report/config fields use `provider_id` /
  `provider_name` / `total_providers` / `providers` (previously school-specific names).
  This is a hard rename with no backward-compatible aliases.
- `canoniq demo` now fails with a clear, actionable message when the bundled
  `examples/` datasets are absent (e.g. a bare `pip install` without the repo)
  instead of a cryptic file-not-found error.
- CI lints `examples/` in addition to `canoniq` and `tests`.

### Removed

- Redundant internal PRD binaries (`*.pdf`/`*.docx`) — superseded by the
  consolidated internal product specification (kept private, not published).

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

[Unreleased]: https://github.com/Buchiexplores/canoniq/compare/v0.3.1...HEAD
[0.3.1]: https://github.com/Buchiexplores/canoniq/releases/tag/v0.3.1
[0.3.0]: https://github.com/Buchiexplores/canoniq/releases/tag/v0.3.0
[0.2.2]: https://github.com/Buchiexplores/canoniq/releases/tag/v0.2.2
[0.2.1]: https://github.com/Buchiexplores/canoniq/releases/tag/v0.2.1
[0.2.0]: https://github.com/Buchiexplores/canoniq/releases/tag/v0.2.0
[0.1.0]: https://github.com/Buchiexplores/canoniq/blob/main/CHANGELOG.md
