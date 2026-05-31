# Security Policy

CanonIQ is local-first and privacy-conscious by design. This document explains
the guarantees the project makes and how to report a vulnerability.

## Design guarantees

- **Local-first by default.** The core package does not send source data,
  schemas, sample values, or mappings to any external service.
- **No telemetry.** The MVP collects and transmits nothing.
- **No external network calls in the core.** The only network path that can ever
  exist is an optional AI adapter that you configure explicitly and opt into.
- **No secrets in the repo.** Source configs reference `${ENV}` variables only.
  The config loader warns on the `canoniq.sources` logger if a value looks like
  an inline secret.
- **Sensitive sample values are masked** before they leave the profiler when
  masking is enabled (the default).
- **Synthetic example data only.** No real personal, health, financial, or
  educational data ships in this repository.
- **Tests make zero network calls**, enforced by a socket guard in the test
  session.

## Supported versions

The latest released minor version receives security fixes. CanonIQ is
pre-1.0; pin a version in production and review release notes before upgrading.

| Version | Supported |
|---------|-----------|
| 0.1.x   | yes       |

## Reporting a vulnerability

Please report suspected vulnerabilities privately to **okekeag@gmail.com**.

Include:

- a description of the issue and its impact,
- steps to reproduce or a proof of concept,
- affected version(s) and environment.

Please do not open a public issue for security reports. We aim to acknowledge a
report within 3 business days and to provide a remediation timeline after triage.
Coordinated disclosure is appreciated: give us a reasonable window to ship a fix
before any public write-up.

## Scope

In scope: the `canoniq` package, CLI, and bundled configuration. Out of scope:
third-party dependencies (report upstream), and the planned enterprise
connectors that are still placeholders in this release.
