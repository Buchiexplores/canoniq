# 06 — Demoing to stakeholders

A practical guide to *presenting* CanonIQ — to executives, customers, or engineers.

---

## Know your audience (tailor the message)

| Audience | What they care about | Lead with |
|---|---|---|
| **Executives** | Time/cost saved, risk reduced | "Cuts data-onboarding from days to minutes, with an audit trail." |
| **Customers / partners** | Easy onboarding, their data is safe | "Upload your file as-is; it stays on our servers; you confirm a couple of fields." |
| **Engineers** | How it works, how to extend | "Explainable signal-based scoring, layered architecture, 92% test coverage." |
| **Security / compliance** | Where data goes | "Local-first. No telemetry. No external calls. Sensitive values masked." |

---

## The 10-minute live demo (script)

> Setup beforehand: a terminal in the repo, virtualenv active. That's it.

**Minute 0–1 — The problem.**
Say: *"Every time we take in data from a new source, someone hand-maps their columns to
ours. It's slow and error-prone. Watch this do it automatically."*

**Minute 1–3 — One command, whole pipeline.**
```bash
canoniq demo finance
```
Point at the output table: *"It profiled the file, suggested 6 mappings, generated 11
validation rules, produced clean rows, and detected drift — in under a second."*

**Minute 3–6 — The explainability (the wow moment).**
Scroll to the mappings and read one reason aloud:
> *"`iban` is a declared alias of `account_id`; types match; pattern matches the IBAN
> format → 90% confidence, auto-approved."*

Then point to the `requires_review` row: *"This one it's less sure about, so instead of
guessing silently, it asks a human. That's the trust model."*

**Minute 6–8 — Run it on 'their' data.**
```bash
canoniq profile --source examples/retail/source_products.csv --out /tmp/p.json
canoniq suggest --profile /tmp/p.json \
  --canonical examples/retail/canonical_product.yml --out /tmp/s.json
```
Say: *"Different industry, different file — same engine, no code change. A new domain is
just a YAML file."*

**Minute 8–9 — The safety net (drift).**
```bash
canoniq drift-check --source examples/retail/new_source_products.csv \
  --mapping /tmp/s.json --canonical examples/retail/canonical_product.yml --out /tmp/d.json
```
Say: *"When a supplier changes their format next month, we find out immediately — before
bad data gets in."*

**Minute 9–10 — The closer.**
*"It runs entirely on our machine. No data leaves. No external AI. Fully auditable. And
it's open source."*

---

## Slide outline (if you need slides)

1. **Title** — CanonIQ: map messy data into trusted models.
2. **The problem** — a screenshot of two spreadsheets with mismatched columns.
3. **The idea** — the kitchen analogy (recipe card + mismatched supplier boxes).
4. **How it works** — the 5-step assembly line diagram (from doc 02).
5. **Demo** — live, or a GIF of `canoniq demo finance`.
6. **Why trust it** — explainable scoring + the review tier + checksums.
7. **Privacy** — local-first, no telemetry, masking.
8. **Extensibility** — new source = 1 connector; new domain = 1 YAML.
9. **Status** — works across 5 industries, 92% test coverage, open source.
10. **Ask** — what you want from the audience (adopt / fund / contribute).

---

## Talking points that land

- **"Explainable, not magic."** Every mapping has a reason a human and an auditor can read.
- **"Confidence with a safety valve."** High-confidence is automatic; uncertain is flagged.
- **"Real checks, not lookalikes."** Bank accounts and product codes are verified with real
  checksum math, not just pattern guesses.
- **"Privacy by architecture."** It can't leak data to a vendor because it doesn't call one.
- **"One engine, every domain."** Industry knowledge lives in YAML, not in code.

---

## Anticipated questions (FAQ)

**Q: Does it use AI / send our data to OpenAI?**
No. The core is local-first and makes no external calls. There's an *optional* AI adapter
that is off by default; you'd have to deliberately enable it.

**Q: What if it maps something wrong?**
Anything below the confidence bar is flagged for review, not applied silently. You set the
bar. And every mapping shows its reasoning, so mistakes are easy to catch.

**Q: How hard is it to add our data model?**
It's a YAML file with field names and aliases — no code. See the onboarding guide.

**Q: What about databases, Snowflake, S3?**
The architecture supports them via connectors; CSV/JSON/JSONL ship today and enterprise
connectors are on the roadmap (the stubs already exist with clear version targets).

**Q: Is it production-ready?**
The core pipeline is stable, typed, and tested (92% coverage), with CI and a Docker image.
It's pre-1.0, so pin a version and review release notes when upgrading.

**Q: How do we measure the benefit?**
Compare hours-per-onboarding before vs. after, and error rates caught by validation. The
drift reports also quantify how often upstream sources change.

---

## Demo checklist

- [ ] Virtualenv active, `canoniq version` works
- [ ] Terminal font large enough to read from the back of the room
- [ ] Pick ONE domain to go deep, mention others briefly
- [ ] Have the reasons string ready to read aloud — it's the highlight
- [ ] End on privacy + extensibility + the ask

Back to the **[guide index](README.md)**.
