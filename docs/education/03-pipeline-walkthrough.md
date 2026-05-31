# 03 — Pipeline walkthrough (a worked example)

Let's follow one real, bundled example all the way through. We'll use the **finance**
domain. Run it yourself any time:

```bash
python examples/finance/demo.py
```

## The cast

**Your canonical model** (`examples/finance/canonical_transaction.yml`) — the shape you
*want*:

| Canonical field | Type | Notes |
|---|---|---|
| `transaction_id` | string | the primary key |
| `account_id` | string | format = IBAN |
| `amount` | decimal | money |
| `amount_currency` | currency_code | must be a real ISO 4217 code |
| `direction` | enum | `debit` or `credit` |
| `booking_datetime` | timestamp | ISO 8601 |

**The messy source** (`examples/finance/source_transactions.csv`) — what actually
arrived. Note the columns are named *differently*:

```
txn_id,iban,txn_amt,currency,drcr,posted_at
TXN1001,GB82WEST12345698765432,250.00,GBP,DBIT,2026-01-04T09:15:00Z
...
```

## Step 1 — Profile ("what's in this file?")

CanonIQ samples the rows and describes each column. For example it learns:
- `iban` holds text values that match an **IBAN-like pattern**
- `txn_amt` holds **decimals**, all positive
- `currency` holds short codes from a tiny set (`GBP`, `EUR`, …) → looks like an **enum**
- `posted_at` holds **ISO-8601 timestamps**

Result: **6 fields profiled.**

## Step 2 — Suggest ("which column maps to which slot?")

Now the matcher scores each source column against the canonical fields. Here's the
*actual* output:

```
        txn_id -> transaction_id    0.90  auto_approved
          iban -> account_id        0.90  auto_approved
       txn_amt -> amount            0.90  auto_approved
      currency -> amount_currency   0.90  auto_approved
          drcr -> direction         0.85  requires_review
     posted_at -> booking_datetime  0.90  auto_approved
```

**Result: 5 auto-approved, 1 needs review.**

### Why did `iban -> account_id` score 0.90?

The reasons string (CanonIQ gives you this for free) says:

> `iban` is a declared alias of `account_id`; name similarity 1.00; types match (string);
> value pattern `iban_like` matches format `iban`.

Three independent signals agreed, so the score is high → auto-approved.

### Why did `drcr -> direction` only score 0.85 (needs review)?

> `drcr` is a declared alias of `direction`; types match; low-cardinality values align
> with canonical enum.

Good evidence, but a notch lower than the others — so instead of silently trusting it,
CanonIQ flags it for a human to confirm. **This is the safety valve.**

### The thresholds that decided the labels

| Score | Label | Meaning |
|---|---|---|
| ≥ 0.90 | `auto_approved` | Confident — use it automatically |
| 0.70–0.89 | `requires_review` | Probably right — ask a human |
| 0.30–0.69 | `low_confidence` | Weak — usually don't use |
| < 0.30 | (unmapped) | No believable match |

These numbers live in config and you can change them.

## Step 3 — Rules ("what must be true?")

From the canonical schema, CanonIQ generates checks, e.g.:
- `transaction_id` is required and must be present
- `amount_currency` must be a valid ISO 4217 code
- `account_id` must pass the **IBAN checksum** (real mod-97 math)
- `direction` must be `debit` or `credit`

**Result: 11 validation rules.**

## Step 4 — Apply ("reshape into my model")

CanonIQ renames the columns to canonical names, converts types, and drops anything
unmapped. The messy row becomes:

```
transaction_id=TXN1001  account_id=GB82WEST12345698765432  amount=250.00
amount_currency=GBP     direction=debit  booking_datetime=2026-01-04T09:15:00Z
```

**Result: 8 clean canonical rows** (we asked it to include the review-tier mapping too).

## Step 5 — Drift ("did the next file change?")

A later file (`new_source_transactions.csv`) arrives — but the provider renamed and added
columns (`value_date`, `channel`, a renamed amount column). CanonIQ re-profiles it and
compares to our saved mapping.

**Result: `drift_detected`** — with a list of exactly what changed, so you fix the
integration before the bad-shaped data gets in.

## The same thing in 6 lines of Python

```python
from canoniq import CanonIQ

engine  = CanonIQ()
profile = engine.profile_source("examples/finance/source_transactions.csv")
mapping = engine.suggest_mappings(profile, "examples/finance/canonical_transaction.yml")
rules   = engine.generate_validation_rules(mapping, "examples/finance/canonical_transaction.yml", profile)
result  = engine.apply_mapping("examples/finance/source_transactions.csv", mapping,
                               "examples/finance/canonical_transaction.yml", include_review=True)
report  = engine.detect_drift("examples/finance/new_source_transactions.csv", mapping,
                              "examples/finance/canonical_transaction.yml")
```

That's the entire product, end to end.

Next: **[04 — Onboarding](04-onboarding.md)**
