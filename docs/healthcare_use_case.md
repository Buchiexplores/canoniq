# Use case: Healthcare

> One of five bundled examples. CanonIQ is domain-agnostic — see the other use-case docs.

## Scenario

A health-data platform receives patient feeds from multiple partner systems. Each uses its own
column names — `mrn` vs `patient_number`, `dob` vs `birth_date`, `sex` vs `administrative_gender`,
`icd10_code` vs `snomed_code` — and every feed carries PHI. The platform needs one canonical
`patient` model with PHI handled safely.

## Canonical model

`examples/healthcare/canonical_patient.yml` tracks **HL7 FHIR R4 Patient**, **US Core**,
**ICD-10-CM**, and **SNOMED CT**: `patient_id` (pk, PHI), `date_of_birth` (PHI), `gender` (enum),
`email` (PHI), `condition_code` (ICD-10 / SNOMED). See [standards_mapping.md](standards_mapping.md).

## Run it

```bash
canoniq demo healthcare
```

## What CanonIQ does

- Maps `mrn`/`medical_record_number` → `patient_id` (the PHI primary key) via aliases.
- Flags `patient_id`, `date_of_birth`, and `patient_email` as **PHI** and masks sample values
  before they leave the profiler — nothing sensitive appears in `profile.json`.
- Enum-checks `gender`; format-checks `email` and `date_of_birth`.
- On a partner switch from ICD-10 to SNOMED (`new_source_patients.csv`), `drift-check` surfaces the
  renamed code column and the added `primary_language` field.

## Privacy

Healthcare data is the sharpest test of CanonIQ's local-first guarantee: no source data, schemas,
or sample values leave the machine, there is no telemetry, and PHI sample values are masked by
default. All bundled data is synthetic.

## Why it matters

Partner onboarding becomes a safe, auditable, FHIR-aligned mapping step instead of a PHI-handling
liability.
