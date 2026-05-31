# Domain packs

A **domain** in CanonIQ is just a canonical-schema YAML plus synthetic example data. The engine has
no domain-specific logic, so adding a domain never touches the core. Five domains ship in v0.1:
higher-ed, retail, healthcare, finance, logistics.

## How a domain is wired

`canoniq/domains/__init__.py` maps each domain key to its files and entity name:

```python
DOMAINS = {
    "higher-ed": {"subdir": "higher_ed", "canonical": "canonical_student.yml",
                  "source": "source_students.csv", "new_source": "new_source_students.csv",
                  "entity": "student"},
    # retail, healthcare, finance, logistics ...
}
```

`domain_paths(domain)` resolves these to absolute paths under `examples/`. The `demo` command and
the end-to-end tests both drive every domain through this map.

## Adding a new domain

Follow these five steps. The HR domain is used as a running example.

### 1. Create the canonical schema YAML

Add `examples/hr/canonical_worker.yml` with production-grade field metadata:

```yaml
domain: hr
entity: worker
version: 1
primary_key: [worker_id]
standards: ["HR Open Standards", "SOC", "ISCO-08"]
fields:
  worker_id:
    type: string
    required: true
    semantic_tags: [identifier]
    aliases: [employee_id, emp_id, person_number, staff_id]
  email:
    type: email
    required: true
    format: email
    pii: moderate
    aliases: [work_email, email_address]
  occupation_code:
    type: string
    required: false
    standard: { name: "ISCO-08", path: "Occupation.code" }
    aliases: [soc_code, job_code, isco]
```

### 2. Add aliases

`aliases` are the strongest matching signal (weight 0.40). List the real-world column names you
expect partners to send for each canonical field. Good aliases turn `requires_review` into
`auto_approved`. See [concepts.md](concepts.md#scoring).

### 3. Add synthetic example data

- `examples/hr/source_workers.csv` — synthetic rows whose column names differ from the canonical
  field names (so matching does real work).
- `examples/hr/new_source_workers.csv` — a **drift variant**: rename/add/remove columns so
  `drift-check` reports `drift_detected`.

**All example data must be synthetic.** Never commit real personal, health, financial, or
educational data. Mask anything PII-shaped.

### 4. Register and test

- Add an `"hr"` entry to `DOMAINS` in `canoniq/domains/__init__.py`.
- The parametrized suite in `tests/test_domain_examples.py` will then run the full pipeline,
  determinism, drift, primary-key-mapping, and no-raw-PII checks for your domain automatically.

### 5. Add `demo` support

Once the domain is in `DOMAINS`, `canoniq demo hr` works with no further code — it profiles,
suggests, generates rules, transforms, and detects drift, writing to `out/worker/`.

## Documentation

Add `docs/<domain>_use_case.md` describing the scenario, the standards it tracks, and the mapping
story end to end. Keep each domain as **one example** — CanonIQ is the product, domains are
illustrations. See the [standards mapping](standards_mapping.md) for which standards each domain
tracks.
