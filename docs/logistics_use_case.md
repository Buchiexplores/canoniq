# Use case: Logistics

> One of five bundled examples. CanonIQ is domain-agnostic — see the other use-case docs.

## Scenario

A shipping-visibility platform aggregates feeds from many carriers. Each carrier names fields its
own way — `shipment_no` vs `load_id`, `tracking_num` vs `carrier_tracking_id`, `carrier` vs
`shipping_provider`, `from_zip` vs `origin_zip`. The platform needs one canonical `shipment` model
so tracking and ETA work across carriers.

## Canonical model

`examples/logistics/canonical_shipment.yml` tracks **GS1 SSCC**, **SCAC**, **ISO 3166**, and
**ISO 8601**: `shipment_id` (pk, SSCC), `tracking_number`, `carrier_scac` (SCAC),
`origin_postal_code` (format `postal_code`), `destination_country` (format `iso3166_alpha2`),
`estimated_delivery_at` (ISO 8601). See [standards_mapping.md](standards_mapping.md).

## Run it

```bash
canoniq demo logistics
```

## What CanonIQ does

- Maps `shipment_no`/`load_id` → `shipment_id` and `carrier`/`shipping_provider` → `carrier_scac`
  via aliases.
- Validates `destination_country` against ISO 3166 alpha-2; format-checks `estimated_delivery_at`
  as ISO 8601.
- On a new carrier feed (`new_source_shipments.csv`: `service_level` added, fields renamed),
  `drift-check` flags the additions and renames.

## Why it matters

Each new carrier integration becomes a quick, standards-aligned mapping review instead of bespoke
feed parsing.
