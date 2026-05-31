# Standards mapping

Each bundled domain's canonical schema tracks recognized industry standards. This table maps every
canonical field to the standard (and path) it represents, so the schemas double as a reference for
how production data models are structured. All schemas live under `examples/<domain>/`.

## Higher education — `student` (OneRoster / Ed-Fi / CEDS)

| Canonical field | Type | Standard · path |
|---|---|---|
| `student_id` | string (pk) | OneRoster · `user.sourcedId` |
| `email` | email | OneRoster · `user.email` |
| `given_name` | string | OneRoster · `user.givenName` |
| `family_name` | string | OneRoster · `user.familyName` |
| `gpa` | decimal (0–4) | CEDS · Cumulative Grade Point Average |
| `enrollment_status` | enum | Ed-Fi · `StudentSchoolAssociation.entryGradeLevel` |
| `last_lms_login` | timestamp | Caliper · `SessionEvent.startedAtTime` |

## Retail — `product` (GS1 GTIN / schema.org / ISO 4217)

| Canonical field | Type | Standard · path |
|---|---|---|
| `product_id` | string (pk), format `gtin` | GS1 · GTIN |
| `product_name` | string | schema.org · `Product.name` |
| `brand` | string | schema.org · `Product.brand` |
| `price` | decimal | money (currency from `price_currency`) |
| `price_currency` | currency_code, format `iso4217` | ISO 4217 |
| `inventory_quantity` | integer | — |

## Healthcare — `patient` (HL7 FHIR R4 / US Core / ICD-10 / SNOMED)

| Canonical field | Type | Standard · path |
|---|---|---|
| `patient_id` | string (pk), PHI | FHIR · `Patient.identifier[type=MR].value` |
| `date_of_birth` | date, PHI | FHIR · `Patient.birthDate` |
| `gender` | enum | FHIR · `Patient.gender` |
| `email` | email, PHI | FHIR · `Patient.telecom[system=email].value` |
| `condition_code` | string | FHIR · `Condition.code.coding` (ICD-10-CM / SNOMED CT) |

## Finance — `transaction` (ISO 20022 / ISO 4217 / IBAN / ISO 8601)

| Canonical field | Type | Standard · path |
|---|---|---|
| `transaction_id` | string (pk) | ISO 20022 · `TxId / EndToEndId` |
| `account_id` | string, format `iban` | ISO 13616 · `DbtrAcct.Id.IBAN` |
| `amount` | decimal | ISO 20022 · `Amt.InstdAmt` |
| `amount_currency` | currency_code, format `iso4217` | ISO 4217 · `Amt.@Ccy` |
| `direction` | enum (debit/credit) | ISO 20022 · `CdtDbtInd` (DBIT/CRDT) |
| `booking_datetime` | timestamp, format `iso8601` | ISO 20022 · `BookgDt / ValDt` |

## Logistics — `shipment` (GS1 SSCC / SCAC / ISO 3166 / ISO 8601)

| Canonical field | Type | Standard · path |
|---|---|---|
| `shipment_id` | string (pk) | GS1 · SSCC |
| `tracking_number` | string | — |
| `carrier_scac` | string | SCAC · Carrier SCAC |
| `origin_postal_code` | string, format `postal_code` | — |
| `destination_country` | string, format `iso3166_alpha2` | ISO 3166 · Country alpha-2 |
| `estimated_delivery_at` | timestamp, format `iso8601` | — |

## Format validators

The `format` key drives a validator. CanonIQ ships checksum-aware validators plus primitives:

| Format | Standard | Check |
|---|---|---|
| `iban` | ISO 13616 | mod-97 checksum |
| `gtin` | GS1 | GS1 check digit |
| `npi` | US NPI | Luhn with 80840 prefix |
| `lei` | ISO 17442 | ISO 7064 mod-97-10 |
| `iso4217` | ISO 4217 | currency code set |
| `iso3166_alpha2` | ISO 3166 | country code set |
| `iso8601` | ISO 8601 | datetime shape |
| `email` | RFC 5322 | email shape |
| `uuid` | RFC 4122 | UUID shape |

## Cross-cutting standards

| Standard | Used for |
|---|---|
| ISO 8601 | datetimes |
| ISO 3166 | country codes |
| E.164 | phone numbers |
| RFC 5322 | email addresses |
| RFC 4122 | UUIDs |

For the full standards glossary see §33 of the PRD.
