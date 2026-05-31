# 02 — Architecture, explained simply

## The big picture

Think of CanonIQ as an **assembly line**. Raw material (a messy file) enters one end,
and a finished product (clean canonical data + a mapping you can trust) comes out the
other. Each station does one job and hands off to the next.

```
  messy source                                          trusted output
      │                                                       ▲
      ▼                                                       │
 ┌─────────┐   ┌──────────┐   ┌─────────┐   ┌────────────┐   ┌───────────┐
 │connector│──▶│ profiler │──▶│ matcher │──▶│ validation │──▶│ transform │
 └─────────┘   └──────────┘   └────┬────┘   └────────────┘   └───────────┘
   reads the     describes      scores &       builds &         reshapes
   raw data      the data       explains       runs checks      into model
                                  │
                                  ▼
                              ┌───────┐
                              │ drift │  compares a later file to the saved mapping
                              └───────┘
```

The whole line is wrapped by two thin "control panels":
- the **SDK** (`CanonIQ` Python class) — for code
- the **CLI** (`canoniq` command) — for the terminal

Both call the *same* engine, so anything you can do in one you can do in the other.

## The layers, one at a time

### 1. Connectors — "read the raw data"
The **only** part that touches a data source. It reads CSV/JSON/JSONL and hands back
plain Python rows (a list of dictionaries). Enterprise sources (databases, cloud
buckets) are stubbed out as *placeholders* that clearly say "not built yet — coming in
version X."

> **Why a hard boundary here?** Because everything downstream works on plain rows. To
> add Postgres support later, you write *one* connector — you never touch the matcher,
> profiler, or anything else. This is the single most important design decision.

### 2. Profiler — "describe the data"
Looks at the rows and computes statistics per column: inferred type, how many values
are empty, how many are unique, value patterns, and **PII flags** (does this look like
an email? a name?). Sensitive sample values are **masked** before they leave this stage.

> **Why mask here?** So no sensitive value can leak into a profile file, a log, or a UI
> downstream. Privacy is enforced at the earliest possible point.

### 3. Matcher + scoring — "score and explain"
For each source column, it runs five small matchers (alias, name, type, pattern, range),
combines their scores with weights, and produces a confidence number plus a list of
human-readable reasons. A threshold then labels each mapping.

> **Why many small matchers instead of one model?** Each matcher is simple, testable, and
> explainable on its own. Adding up transparent signals beats one opaque guess.

### 4. Validation — "build and run checks"
From your canonical schema it generates rules: required fields must be present, types
must match, enums must be from the allowed list, numbers must be in range, and special
formats must pass a **checksum** (e.g. an IBAN bank account number is verified with the
real mod-97 algorithm — not just "does it look like an IBAN").

### 5. Transform — "reshape into the model"
Renames source columns to canonical field names, converts types, and drops columns that
weren't mapped. Output is clean canonical rows.

### 6. Drift — "did the next file change?"
When a *new* file arrives later, it re-profiles it and compares against the mapping you
saved. It reports renamed columns, new columns, removed columns, and type changes — so
you fix the integration *before* bad data flows through.

## The supporting cast

- **core/models.py** — the typed data shapes (Pydantic) that flow between stations. Every
  output serializes to clean, stable JSON.
- **config.py** — the dials: thresholds, signal weights, sample size, masking on/off.
- **registry/** — loads canonical-schema YAML and saves/loads mappings.
- **sources/** — loads a "source config" YAML and fills in secrets from environment
  variables (never hard-coded).
- **domains/** — the five bundled examples (just data + schema, no logic).

## Why this shape scales

- **New data source?** Add a connector. Nothing else changes.
- **New industry/model?** Add a YAML schema + synthetic data. No code.
- **Tune behavior?** Change weights/thresholds in config. No code.
- **Audit a decision?** Read the `reasons` on any mapping.

Each kind of change is isolated to exactly one place. That's the payoff of the layered,
boundary-respecting design.

## A note on data shapes (so the rest makes sense)

Three objects you'll see everywhere:

- **SourceProfile** — the description of an incoming file.
- **CanonicalEntity** — your target model (loaded from YAML).
- **MappingResult** — the list of scored suggestions tying the two together.

Once you know those three, the SDK reads like the assembly line above.

Next: **[03 — Pipeline walkthrough (worked example)](03-pipeline-walkthrough.md)**
