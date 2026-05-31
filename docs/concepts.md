# Concepts

CanonIQ has a small set of core ideas. Understanding them makes the CLI and SDK predictable.

## Source profile

A **profile** is the structure and statistics of a sampled source dataset. The profiler reads up
to `sample_limit` records and produces a `SourceProfile` containing one `SourceFieldProfile` per
field:

- `inferred_type` — first-match type inference (boolean, integer, decimal, date, timestamp,
  email, string, …).
- `null_rate`, `unique_rate`, `distinct_count`, `min`/`max`, `avg_str_len`.
- `patterns` — detected shapes (e.g. an email pattern, a UUID pattern).
- `pii_flags` — categories such as `email`, `phone`, `name`, `phi`. High-PII/PHI sample values
  are **masked** before they leave the profiler when `mask_pii` is on (the default).
- `enum_candidates` — small, repeating value sets that look enum-like.

Profiles are pure data: deterministic and JSON-serializable.

## Canonical schema

A **canonical schema** (`CanonicalEntity`) is the target model you map onto. It is versioned YAML
with production-grade metadata per field:

```yaml
domain: higher_ed
entity: student
version: 1
primary_key: [student_id]
standards: ["1EdTech OneRoster 1.2", "Ed-Fi", "CEDS"]
fields:
  email:
    type: email
    required: true
    format: email          # drives a format validator
    pii: moderate          # informs masking + validation severity
    standard: { name: "OneRoster", path: "user.email" }
    aliases: [student_email, email_address, primary_email]
```

Key field keys: `type`, `required`, `aliases`, `min`/`max`, `enum`, `unit`, `format`, `pii`,
`standard`, `semantic_tags`. `aliases` are the single most powerful matching signal — invest in
them. See [domain_packs.md](domain_packs.md).

## Mapping suggestions

For each source field the engine emits a `MappingSuggestion`: the chosen `canonical_field`
(or `None`), a `confidence` in `[0,1]`, a `status`, human-readable `reasons`, and the raw
`signals` that produced the score.

### Scoring

Confidence is a weighted sum of matcher signals, normalized over the active (non-zero) weights and
clamped to `[0,1]`:

| Signal | Default weight | What it measures |
|---|---|---|
| alias | 0.40 | source name matches a canonical alias |
| name | 0.20 | fuzzy similarity to the canonical field name |
| type | 0.15 | inferred type agrees with canonical type |
| pattern | 0.15 | detected pattern matches the canonical format |
| range | 0.10 | numeric values fall within canonical min/max |
| semantic | 0.00 | optional AI adapter (off by default) |

Weights, thresholds, and sampling live in `CanonIQConfig` and can be overridden.

### Status gating

A suggestion's `status` is derived from its confidence:

- `>= auto_approve_threshold` (default **0.90**) → `auto_approved`
- `>= review_threshold` (default **0.70**) → `requires_review`
- below that but `>= mapping_floor` (default **0.30**) → `low_confidence`
- below the floor → no canonical field is assigned

`MappingResult.approved_mappings(include_review=...)` returns the usable `{source: canonical}`
map, optionally including the review tier.

## Validation rules

From the canonical schema + suggestions (+ optional profile) CanonIQ generates `ValidationRule`s:
required-field presence, type checks, enum membership, range bounds, and **format checksums**:

- IBAN (ISO 13616, mod-97)
- GTIN (GS1 check digit)
- NPI (Luhn with the 80840 prefix)
- LEI (ISO 17442, ISO 7064 mod-97-10)
- plus primitives: ISO 8601 datetime, ISO 3166 country, RFC 5322 email, RFC 4122 UUID.

Running the validator over records yields a `ValidationReport` of `ValidationFinding`s.

## Transformation

`apply_mapping` produces canonical records: it renames source fields to canonical fields, coerces
types, drops unmapped fields (unless `keep_unmapped=True`), and can include review-tier mappings
with `include_review=True`.

## Drift

When a later ingestion arrives, `detect_drift` re-profiles it and compares against the prior
mapping/schema, reporting:

- `missing_fields` — previously mapped source fields now gone.
- `new_fields` — source fields not seen before.
- `type_changes` — fields whose inferred type changed.
- `unmapped_required` — required canonical fields no longer covered.
- `suggested_remappings` — proposals to re-map renamed fields.

`status` is `ok` when nothing diverges, otherwise `drift_detected`.

See [architecture.md](architecture.md) for how these pieces fit together in code.
