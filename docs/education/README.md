# CanonIQ — Education & Onboarding Guide

A plain-English guide to *what* CanonIQ is, *why* it's built the way it is, and *how*
to use, extend, and present it. Start at the top and read down — each doc builds on
the previous one.

## Learning path

1. **[01 — What it is & why](01-what-and-why.md)**
   The problem in one sentence, a kitchen analogy, the approach, and the rationale.

2. **[02 — Architecture, explained simply](02-architecture.md)**
   The layers, what each one does, and *why* each design decision was made.

3. **[03 — Pipeline walkthrough (worked example)](03-pipeline-walkthrough.md)**
   One messy CSV followed all the way through to clean canonical output, with real numbers.

4. **[04 — Onboarding](04-onboarding.md)**
   For users (run it in 5 minutes) and for developers (set up, test, extend).

5. **[05 — Use cases (with examples)](05-use-cases.md)**
   Concrete scenarios across five industries plus SaaS onboarding and AI agents.

6. **[06 — Demoing to stakeholders](06-stakeholder-demo.md)**
   A 10-minute demo script, talking points, slide outline, and an FAQ.

7. **[07 — The 360° Architecture (deep dive)](07-architecture-360.md)**
   The complete map: every layer and component, the exact data that flows between them,
   the rationale for each, an end-to-end trace with real numbers, and how to present it.
   Readable at three altitudes — beginner, practitioner, expert.

## The 30-second version

CanonIQ takes a *messy* spreadsheet or data file from someone else and figures out how
its columns line up with *your* official data model — automatically, with a confidence
score and a plain-English reason for every guess. Then it cleans the data into your
shape, checks it against rules, and warns you when a future file arrives shaped
differently.

It runs entirely on your machine. No data is sent anywhere.
