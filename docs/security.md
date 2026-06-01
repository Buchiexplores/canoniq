# Privacy & Security

CanonIQ is built to be safe to run on **real, sensitive data** — student records,
patient data, financial transactions, customer PII — inside regulated organizations.
This guide explains exactly how it handles privacy, PII/PHI, secrets, and data egress,
and what that means for adopting it in industry.

> **TL;DR** — CanonIQ is **local-first**: by default your source data, schemas, sample
> values, and mappings never leave the machine it runs on. There is no telemetry and
> no network call in the core. Sensitive sample values are **masked by default**. The
> only path that can ever reach the network is an **optional AI adapter you explicitly
> turn on**, and even then it sends *field names and schema text only — never your
> data values*.

---

## 1. Local-first by default

The core package (`canoniq` with its default dependencies) performs **all profiling,
mapping, validation, transformation, and drift detection in-process, on your machine**.

- **No data egress.** Source files are read locally; results are written locally.
  Nothing is uploaded anywhere.
- **No telemetry.** CanonIQ collects and transmits no usage data, ever.
- **No network calls in the core.** The default install makes zero outbound
  connections. This is enforced in CI: the **test suite runs behind a socket guard**
  that fails the build if any test opens a network socket.
- **No hidden services.** It's a library + CLI, not a daemon. It runs where you run
  it — your laptop, a CI runner, a locked-down VPC, an air-gapped host.

This makes CanonIQ suitable for environments where data residency and "data never
leaves our perimeter" are hard requirements.

---

## 2. PII / PHI detection

During profiling, CanonIQ flags fields that look like personal or health data, using
**local heuristics over the field name and a small sample of values** (no external
service). Detected flags include:

| Flag | Triggered by (examples) |
|---|---|
| `email` | `email`, `e_mail`; values matching an email pattern |
| `phone` | `phone`, `mobile`, `cell`, `telephone`, `fax` |
| `name` | `first_name`, `last_name`, `given_name`, `surname`, `fname`/`lname` |
| `national_id` | `ssn`, `social_security`, `national_id`, `tax_id`, `passport`; SSN-shaped values |
| `dob` | `dob`, `birth_date`, `date_of_birth` |
| `address` | `address`, `street`, `postal`, `zip` |
| `mrn` | `mrn`, `medical_record` (medical record number — PHI) |
| `account_number` | `account_number`, `acct_num`, `iban`, `card_number` |
| `ip_address` | `ip_address`, `client_ip`; dotted-quad values |

**High-sensitivity flags** — `national_id`, `mrn`, `account_number` — always trigger
masking. Canonical schema fields can additionally declare a **sensitivity level** via
`pii:` (`none` · `low` · `moderate` · `high` · `phi`) to document intent and drive
your own downstream policy.

Detection is intentionally **conservative and transparent**: it's a heuristic aid, not
a guarantee of completeness. You remain responsible for classifying your own data —
but you start from automatic flags rather than a blank slate.

---

## 3. Masking sensitive sample values

CanonIQ keeps a few **sample values** per field (default 5) purely to infer types and
patterns. Any sample value on a sensitive field is **masked before it leaves the
profiler** — so even the in-memory profile and the JSON profile artifact never contain
raw PII/PHI.

- Masking is **on by default** (`mask_pii: true`).
- It applies to high-PII flags **and** moderate ones (`email`, `name`, `dob`,
  `address`, `phone`, `ip_address`) — privacy-safe by default.
- Masking style: emails become `j***@***`; other values keep the first character and
  redact the rest (`N10001` → `N*****`).

```text
raw value         flags           masked sample
----------------  --------------  ---------------
jane@school.edu   [email]         j***@***
N10001            [mrn]           N*****
123-45-6789       [national_id]   1**********
4111111111111111  [account_number] 4***************
```

(The rule: emails keep the first local char and redact the rest; everything else keeps
the first character and redacts the remainder.)

Masking affects **profiles and explanations only** — the actual transformation step
still produces correct canonical records from your real local data. Masking is about
what shows up in *artifacts and logs*, not about corrupting your output.

> You can disable masking (`mask_pii: false`) for fully-trusted local debugging, but
> the default is to mask.

---

## 4. The optional AI adapter — and what it does (and doesn't) send

CanonIQ's mapping is **deterministic and offline by default**. An optional *semantic*
signal can improve fuzzy matching, and it's the **only** feature that can ever touch
the network. It is **off unless you explicitly configure it.**

Two flavors:

- **Local embeddings** (`sentence-transformers`, the `[ai]` extra) — runs **entirely
  on your machine**. No network at all. Best for regulated/air-gapped use.
- **Hosted embeddings** (OpenAI, Gemini) — call a third-party API. **Opt-in**, selected
  declaratively in config.

**Critical privacy property — what gets sent to a hosted provider:** only **source
field *names*** and **canonical schema metadata** (the canonical field name, its
aliases, semantic tags, and description). **Sample values are never sent — not even
masked ones.** So no PII/PHI value, and no row of your data, ever reaches an external
API, even with a hosted model enabled. (See `canoniq/ai/_text.py`, which centralizes
exactly what text an embedding model is allowed to see.)

Per-text embeddings are cached, so a run makes roughly *(unique source names + unique
canonical fields)* calls — not one per candidate pair.

If your policy forbids any external calls, simply **don't enable a hosted adapter** (or
use the local one). The core never initiates a connection on its own.

---

## 5. Secret management

CanonIQ never wants your secrets in a file it reads.

- **Source configs use `${ENV}` interpolation.** Connection strings, keys, and
  passwords are referenced as `${MY_VAR}` and resolved from the environment at load
  time — never written inline.
- **Inline-secret warning.** If a sensitive-looking key (`password`, `secret`, `token`,
  `api_key`, `private_key`, `credentials`, …) holds a literal value instead of an
  `${ENV}` reference, the loader emits a warning on the `canoniq.sources` logger so the
  leak is caught early.
- **AI API keys come from the environment**, via a variable *named* in config
  (`api_key_env: OPENAI_API_KEY`). The key value is never stored in the config file.
- **No secrets in this repository.** All bundled example data is synthetic; configs
  reference `${ENV}` only.

---

## 6. Determinism, explainability & auditability

For governance, every CanonIQ decision is reproducible and inspectable:

- **Deterministic.** The same inputs + config always produce the same mappings and
  scores — no nondeterministic model in the default path.
- **Explained.** Every suggested mapping carries human-readable *reasons* (which signal
  fired and how strongly), so a reviewer or auditor can see *why* a field was mapped.
- **Versioned, self-contained artifacts.** Profiles, mappings, validation rules, drift
  reports, and readiness reports are written as stable JSON/YAML stamped with the
  `canoniq_version` that produced them — easy to archive, diff, and attach to a change
  request or audit trail.
- **Human-in-the-loop gating.** Low-confidence mappings are *held back*, not guessed;
  uncertain ones are *flagged for review*. Automation never silently invents a mapping.

---

## 7. Using CanonIQ in regulated industries

CanonIQ's design lines up with the controls these environments care about. CanonIQ
itself is not a compliance certification — it's a tool whose architecture *supports*
your compliance posture:

| Concern | How CanonIQ helps |
|---|---|
| **Data residency / sovereignty** | Local-first; data never leaves your perimeter (no hosted AI required). |
| **HIPAA / PHI** (healthcare) | `mrn` and clinical fields flagged; sensitive samples masked; runs inside your environment so no BAA-triggering third party is involved by default. |
| **GDPR / data minimization** | Only field names + schema text are ever eligible to leave (and only if you opt into a hosted adapter); sample values are minimized and masked. |
| **PCI-DSS** (payments) | `account_number` / card-like fields flagged and masked; no cardholder values transmitted. |
| **SOC 2 / change management** | Deterministic, versioned, explained artifacts make reviews and audits straightforward. |
| **Least privilege** | Secrets via `${ENV}` only; no credentials at rest in configs or the repo. |

### Recommended deployment hardening

- Run in an **isolated environment** (container/VPC) with **only the read access** to
  the sources you're profiling.
- Prefer the **local embedding adapter** (or none) over hosted models when handling
  regulated data.
- Treat the generated **artifacts as sensitive** if you disabled masking — store them
  with the same controls as the source data.
- Pin a version in production (`canoniq==X.Y.Z`) and review release notes before
  upgrading; CanonIQ is pre-1.0.
- Manage source credentials with a secrets manager and inject them as environment
  variables; never commit them.
- Keep dependencies patched (the repo ships Dependabot config and a CI matrix).

---

## 8. Reporting a vulnerability

Found a security issue? Please report it **privately** — do not open a public issue.
See [`SECURITY.md`](../SECURITY.md) for the disclosure process and supported versions.

---

## See also

- [SECURITY.md](../SECURITY.md) — vulnerability disclosure policy & supported versions
- [concepts.md](concepts.md) — profiling, matching, scoring, drift
- [sources.md](sources.md) — source configs, `${ENV}` secrets, sampling
- [onboarding.md](onboarding.md) — enterprise adoption & scalability
