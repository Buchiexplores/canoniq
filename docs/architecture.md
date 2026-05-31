# Architecture

CanonIQ is a small, layered, local-first library. Every layer is typed (Pydantic v2) and pure
where possible. The CLI and SDK are thin wrappers over the same engine.

## Data flow

```
source (file / db / cloud)
        │   connectors/  (source-agnostic boundary)
        ▼
   records: list[dict]
        │   profiler/  → SourceProfile
        ▼
   SourceProfile ───────────────┐
        │   registry/           │
        ▼                       │
   CanonicalEntity              │
        │   matcher/ + scoring/ │
        ▼                       │
   MappingResult ◄──────────────┘
        │
        ├── validation/  → ValidationRule[] → ValidationReport
        ├── transform/   → TransformResult (canonical records)
        └── drift/       → DriftReport  (re-profiles a new source)
```

## Modules

| Module | Responsibility |
|---|---|
| `canoniq/engine.py` | `CanonIQ` SDK facade — orchestrates every stage. |
| `canoniq/cli.py` | Typer CLI (`profile`, `suggest`, `rules`, `apply`, `drift-check`, `demo`, `version`). |
| `canoniq/config.py` | `CanonIQConfig`: thresholds, scoring weights, sampling, masking. |
| `canoniq/core/` | Pydantic models (`models.py`) and constants (`constants.py`). |
| `canoniq/connectors/` | Data-access adapters. Real: CSV/JSON/JSONL. Placeholders: enterprise sources. |
| `canoniq/sources/` | Source-config YAML loader with `${ENV}` interpolation. |
| `canoniq/profiler/` | Source-agnostic profiling: type inference, pattern detection, PII masking. |
| `canoniq/registry/` | Canonical-schema YAML loader/validator + mapping registry (save/load). |
| `canoniq/matcher/` | Alias/name/type/pattern/range matchers + the mapping engine. |
| `canoniq/scoring/` | Weighted confidence scoring. |
| `canoniq/validation/` | Rule generation, format validators (with checksums), validator. |
| `canoniq/transform/` | Transformation to canonical records. |
| `canoniq/drift/` | Drift detection across ingestions. |
| `canoniq/ai/` | Optional AI adapter interface + no-op default (off by default). |
| `canoniq/domains/` | The five bundled domain examples (path resolution for demos/tests). |

## Design principles

- **Local-first.** No source data, schemas, or mappings leave the machine in the core. No
  telemetry. The only network path is an optional, explicitly-configured AI adapter.
- **Source-agnostic boundary.** Everything above `connectors/` works on `list[dict]`; adding a new
  source means adding one connector, not touching the pipeline.
- **Domain-agnostic core.** Domains are just canonical-schema YAML + synthetic data. The engine has
  no domain-specific logic.
- **Deterministic & explainable.** Same input → same suggestions. Every suggestion carries reasons
  and raw signals. Golden-file tests pin determinism across all five domains.
- **Typed & immutable-friendly.** Stages return new model instances rather than mutating inputs.

## Extending

- New data source → [connectors.md](connectors.md).
- New domain → [domain_packs.md](domain_packs.md).
- New source-config type → [sources.md](sources.md).
