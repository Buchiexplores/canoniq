# Use case: Higher education

> Higher education is **one example** of what CanonIQ does — not the product. The same engine maps
> retail, healthcare, finance, and logistics data. See the other use-case docs.

## Scenario

A student-success platform onboards a new institution. The institution exports students from its
SIS/LMS, but every school names columns differently: `emplid` vs `banner_id` vs `student_number`,
`first_name` vs `fname`, `cumulative_gpa` vs `overall_gpa`. The platform needs every export to land
in one canonical `student` model so downstream analytics and interventions just work.

## Canonical model

`examples/higher_ed/canonical_student.yml` tracks **1EdTech OneRoster 1.2**, **Ed-Fi**, and **CEDS**:
`student_id` (pk), `email`, `given_name`, `family_name`, `gpa` (0–4), `enrollment_status` (enum),
`last_lms_login` (ISO 8601). See [standards_mapping.md](standards_mapping.md).

## Run it

```bash
canoniq demo higher-ed
```

Or step through:

```bash
canoniq profile --source examples/higher_ed/source_students.csv --out profile.json
canoniq suggest --profile profile.json --canonical examples/higher_ed/canonical_student.yml --out suggestions.json
canoniq apply   --source examples/higher_ed/source_students.csv --mapping suggestions.json \
                --canonical examples/higher_ed/canonical_student.yml --out canonical.csv --include-review
```

## What CanonIQ does

- Maps `emplid`/`sis_id` → `student_id` with high confidence via aliases, auto-approving the
  primary key.
- Flags `student_email` as PII and masks sample values before they leave the profiler.
- Range-checks `gpa` against `0.0–4.0`; enum-checks `enrollment_status`.
- On the next term's export (`new_source_students.csv`), `drift-check` reports renamed/added
  columns so the integration is fixed before bad data lands.

## Why it matters

Every new school becomes a few minutes of review instead of a bespoke ETL project — and each
mapping is explainable and auditable.
