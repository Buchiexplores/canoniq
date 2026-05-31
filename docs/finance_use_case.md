# Use case: Finance

> One of five bundled examples. CanonIQ is domain-agnostic — see the other use-case docs.

## Scenario

A treasury/reconciliation system ingests transaction files from many banks and payment providers.
Each file labels things differently — `txn_id` vs `transaction_ref`, `iban` vs `account_number`,
`txn_amt` vs `payment_amount`, `drcr` vs `dc_indicator`. The system needs one canonical
`transaction` model aligned to ISO 20022 so reconciliation is consistent.

## Canonical model

`examples/finance/canonical_transaction.yml` tracks **ISO 20022**, **ISO 4217**, **ISO 13616 IBAN**,
and **ISO 8601**: `transaction_id` (pk), `account_id` (format `iban`), `amount` (money),
`amount_currency` (format `iso4217`), `direction` (debit/credit), `booking_datetime` (ISO 8601).
See [standards_mapping.md](standards_mapping.md).

## Run it

```bash
canoniq demo finance
```

## What CanonIQ does

- Maps `iban`/`account_number` → `account_id` and validates the **IBAN mod-97 checksum** (bundled
  data uses real, valid IBAN check digits).
- Validates `amount_currency` against ISO 4217; enum-checks `direction`; format-checks
  `booking_datetime` as ISO 8601.
- Flags `account_id` as moderate PII.
- On a provider switch (`new_source_transactions.csv`: `value_date`, `channel`, renamed amount
  column), `drift-check` reports the changes before they corrupt reconciliation.

## Why it matters

Onboarding a new bank or PSP becomes a checksum-validated, ISO 20022-aligned mapping review instead
of brittle per-bank parsing.
