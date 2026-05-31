# 05 — Use cases (with examples)

CanonIQ fits anywhere you **repeatedly receive data from outside** and need it in
**your** shape. Below: the five bundled domains, plus two cross-cutting patterns.

For each, the pattern is identical: *messy source columns* → *your canonical fields*.

---

## 1. Higher education — onboarding a new school

**Scenario:** A student-success platform adds a new university. The school exports
students, but names columns its own way.

| Their column | Maps to | How |
|---|---|---|
| `emplid` | `student_id` | alias match |
| `student_email` | `email` | alias + email pattern |
| `cumulative_gpa` | `gpa` | alias + range 0.0–4.0 |

**Payoff:** Each new school is a few minutes of review instead of a custom ETL project.
Try it: `python examples/higher_ed/demo.py`

---

## 2. Retail — normalizing supplier catalogs

**Scenario:** A marketplace ingests product feeds from many suppliers.

| Their column | Maps to | How |
|---|---|---|
| `sku` / `upc` / `ean` | `product_id` | alias + **GTIN checksum** |
| `sale_price` | `price` | alias + decimal type |
| `mfr` | `brand` | alias |

**Payoff:** Supplier onboarding becomes a checksum-validated pipeline instead of a
per-vendor spreadsheet. Try it: `python examples/retail/demo.py`

---

## 3. Healthcare — aligning partner patient feeds

**Scenario:** A health-data platform receives patient records from partner systems, and
the data is sensitive.

| Their column | Maps to | How |
|---|---|---|
| `mrn` | `patient_id` | alias |
| `dob` | `date_of_birth` | alias + date type |
| `sex` | `gender` | alias + enum |

**Extra:** sensitive fields are flagged and their sample values are **masked** before
they ever appear in a profile or log. **Payoff:** safe, auditable, standards-aligned
mapping. Try it: `python examples/healthcare/demo.py`

---

## 4. Finance — reconciling bank/payment files

**Scenario:** A treasury system ingests transaction files from many banks.

| Their column | Maps to | How |
|---|---|---|
| `iban` | `account_id` | alias + **IBAN mod-97 checksum** |
| `txn_amt` | `amount` | alias + decimal |
| `drcr` | `direction` | alias + enum (needs review) |

**Payoff:** Onboarding a new bank becomes a checksum-validated mapping review.
Try it: `python examples/finance/demo.py`

---

## 5. Logistics — unifying carrier feeds

**Scenario:** A shipping-visibility platform aggregates feeds from many carriers.

| Their column | Maps to | How |
|---|---|---|
| `shipment_no` | `shipment_id` | alias |
| `carrier` | `carrier_scac` | alias |
| `ship_to_country` | `destination_country` | alias + ISO 3166 check |

**Payoff:** Each new carrier is a quick mapping review. Try it:
`python examples/logistics/demo.py`

---

## 6. SaaS onboarding (cross-cutting)

**Scenario:** Your SaaS lets every customer upload a CSV during onboarding. Each
customer's file looks different.

**With CanonIQ:** the upload is profiled, auto-mapped to your internal schema, validated,
and transformed — automatically. Only low-confidence columns are surfaced to the
customer/support team. Onboarding goes from "send us your file and wait days" to
"upload and confirm a couple of fields."

```python
profile = engine.profile_source(customer_upload)
mapping = engine.suggest_mappings(profile, "internal_model.yml")
needs_review = [m for m in mapping.mappings if m.status == "requires_review"]
# show only `needs_review` to the user; auto-apply the rest
```

---

## 7. AI agent platforms (cross-cutting)

**Scenario:** An AI agent needs to ingest an arbitrary file and load it into a known
schema — but you don't want the agent to "hallucinate" a mapping.

**With CanonIQ:** the agent calls CanonIQ as a **deterministic, explainable tool**. It
gets back scored mappings with reasons. The agent can auto-apply high-confidence ones and
ask the user only about uncertain ones — and every decision is auditable.

> Because the core is local-first and makes no external calls, the agent's data never
> leaves your environment during mapping.

---

## The common shape

Every use case above is the same three lines conceptually:

```
profile the file  →  suggest mappings to my model  →  apply + validate
```

The only thing that changes between industries is the **canonical YAML** — not the code.

Next: **[06 — Demoing to stakeholders](06-stakeholder-demo.md)**
