# 01 — What it is & why

## The problem, in one sentence

Every time you receive data from someone else, their column names, types, and
conventions are different from yours — and reconciling them by hand is slow,
error-prone, and impossible to audit.

## A kitchen analogy

Imagine you run a restaurant with a strict recipe card (your **canonical model**).
The recipe says you need: `flour`, `sugar`, `eggs`, `butter`.

Now five different suppliers deliver ingredients, each with their own labels:

- Supplier A sends boxes labelled `wheat_flour`, `cane_sugar`, `whole_eggs`, `unsalted_butter`
- Supplier B sends `flr`, `sgr`, `egg_qty`, `btr`
- Supplier C writes everything in French.

Before you can cook, someone has to stand at the loading dock and match every
delivered box to a slot on the recipe card. That matching job — done for *data
columns* instead of ingredients — is exactly what CanonIQ automates.

It looks at each incoming "box" (column), and says:

> "`wheat_flour` is almost certainly your `flour` slot — I'm 95% sure, because the
> name is a known alias and the contents look like flour. Auto-approved."

> "`btr` *might* be `butter` — I'm 78% sure. Please double-check."

## What CanonIQ actually produces

Given a source file and your canonical schema, it produces five things in order:

| Step | Plain English | Output |
|---|---|---|
| **Profile** | "What's in this file?" | Column names, types, patterns, sensitive-data flags |
| **Suggest** | "Which column maps to which slot?" | Scored, explained mappings |
| **Rules** | "What must be true for the data to be valid?" | A list of checks |
| **Apply** | "Reshape the data into my model." | Clean canonical rows |
| **Drift** | "Did the next file change shape?" | A diff report |

## The approach: signals, not magic

CanonIQ does **not** rely on a black-box AI guessing answers. It combines several
simple, explainable **signals** and adds them up into a confidence score:

- **Alias match** — does the column name match a known nickname for a canonical field?
  (e.g. `dob` is a known alias of `date_of_birth`)
- **Name similarity** — how close is the spelling? (`emial` ≈ `email`)
- **Type match** — do the values look like the expected type? (numbers vs text vs dates)
- **Pattern match** — do the values fit a known shape? (an email pattern, an IBAN pattern)
- **Range match** — do numbers fall in the expected range? (a GPA between 0 and 4)

Each signal has a weight. The biggest is the alias match, because a curated alias list
is the strongest evidence you can have. The final score decides whether a mapping is
**auto-approved**, **needs review**, or **too uncertain to use**.

## Why build it this way? (Rationale)

| Decision | Why |
|---|---|
| **Explainable scoring** | A human reviewer (and an auditor) can see *why* every mapping was chosen. Trust comes from transparency, not from a confident-sounding guess. |
| **Local-first, no telemetry** | The data being mapped is often sensitive (patient records, transactions). It must never leave the machine. This is a feature, not a limitation. |
| **Domain-agnostic core** | The engine has zero industry-specific logic. A "domain" is just a YAML file. Add healthcare, retail, or your own model without touching the engine. |
| **Source-agnostic boundary** | Everything above the connector layer works on plain rows. Adding a new data source (a database, a cloud bucket) never changes the matching logic. |
| **Deterministic** | The same input always produces the same output. That makes it testable, auditable, and safe to put in a pipeline. |
| **Typed & tested** | Pydantic models and a test suite (92% coverage) mean breakages are caught early. |

## What it is *not*

- It is **not** an ETL scheduler. It produces mappings and transformed output; you decide
  when and where to run it.
- It is **not** a data warehouse. It's the *translation layer* in front of one.
- It does **not** phone home or call external AI by default. An optional AI adapter exists,
  but it's off unless you turn it on.

Next: **[02 — Architecture, explained simply](02-architecture.md)**
