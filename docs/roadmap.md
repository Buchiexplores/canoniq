# Roadmap

CanonIQ ships a complete, local-first MVP in v0.1 and expands connector coverage from there. The
core engine (profile → suggest → rules → transform → drift) is stable; later versions turn
placeholder connectors into real ones and add workflow features.

| Version | Theme | Highlights |
|---|---|---|
| **v0.1** | MVP core | Generic engine; CSV/JSON/JSONL connectors; type/pattern/PII profiling; matching + scoring + explanations; validation; transform; drift; CLI + SDK; 5 domain examples; source-config; placeholder connectors; CI / Docker / docs. |
| **v0.2** | Rich files + DBs | Parquet, Excel, folder sampling; Postgres, MySQL, SQLite (real); approved-mapping promotion workflow (CLI). |
| **v0.3** | Cloud warehouses + lakes | BigQuery, Snowflake, Redshift, Databricks; S3, GCS, Azure Blob; native metadata-assisted matching. |
| **v0.4** | SaaS / API | Salesforce, Canvas, Shopify, Stripe, HubSpot, Workday, generic REST/GraphQL. |
| **Future** | Platform | Server/API mode; review UI; semantic AI matching (local + hosted adapters); lineage/metadata columns; domain packs as installable distributions. |

## Principles that won't change

- **Local-first by default.** Network access only ever via an explicitly-configured AI adapter.
- **No telemetry.**
- **Domain-agnostic, source-agnostic core.** New domains and sources are additive, never core
  rewrites.
- **Deterministic and explainable** mappings, pinned by golden-file tests.

Want a connector or domain sooner? See [connectors.md](connectors.md) and
[domain_packs.md](domain_packs.md), and open an issue or PR.
