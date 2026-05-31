# Use case: Retail

> One of five bundled examples. CanonIQ is domain-agnostic — see the other use-case docs.

## Scenario

A marketplace ingests product catalogs from many suppliers. Each supplier sends a different feed:
`sku_id` vs `upc` vs `item_id` for identity, `sale_price` vs `list_price` for price, `mfr` vs
`brand_name` for brand. The marketplace needs one canonical `product` model so search, pricing, and
inventory work across every supplier.

## Canonical model

`examples/retail/canonical_product.yml` tracks **GS1 GTIN**, **schema.org/Product**, and **ISO 4217**:
`product_id` (pk, format `gtin`), `product_name`, `brand`, `price` (money), `price_currency`
(format `iso4217`), `inventory_quantity`. See [standards_mapping.md](standards_mapping.md).

## Run it

```bash
canoniq demo retail
```

Both CSV and JSON sources are bundled (`source_products.csv`, `source_products.json`), exercising
two real connectors.

## What CanonIQ does

- Maps `sku`/`upc`/`ean` → `product_id` and validates the GS1 **GTIN check digit**.
- Validates `price_currency` against the ISO 4217 enum; range-checks `price` ≥ 0.
- Normalizes brand/name variants to canonical fields with explained confidence.
- On a renamed feed (`new_source_products.csv`: `sku_id`→`product_sku`, `sale_price`→`list_price`,
  added `category`), `drift-check` flags the rename and the new field.

## Why it matters

Supplier onboarding stops being a per-vendor mapping spreadsheet and becomes a reviewable,
checksum-validated pipeline.
