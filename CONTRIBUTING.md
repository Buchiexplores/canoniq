# Contributing to CanonIQ

Thanks for your interest in CanonIQ! Contributions of all kinds are welcome — connectors, domains,
docs, tests, and bug fixes.

## Ground rules

CanonIQ is **local-first and privacy-conscious**. Contributions must preserve these guarantees:

- No network calls in the core package or in tests (a socket guard enforces zero network in the
  test session).
- No telemetry.
- **Synthetic example data only** — never commit real personal, health, financial, or educational
  data.
- **No secrets in the repo** — source configs reference `${ENV}` variables only.
- High-PII/PHI sample values must be masked before they leave the profiler.

## Development setup

```bash
git clone https://github.com/okyke-technologies/canoniq.git
cd canoniq
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Before you open a PR

Run the full check suite locally — CI runs the same:

```bash
ruff check canoniq tests        # lint
mypy canoniq                    # type-check
pytest --cov=canoniq --cov-report=term-missing   # tests; ≥80% coverage, zero network
```

All three must pass. New code needs tests; coverage must stay at or above 80%.

## Project conventions

- Python 3.10+; full type annotations on public signatures.
- Pydantic v2 models for all public data structures.
- Prefer many small, focused modules over large ones.
- Return new objects rather than mutating inputs.
- Keep the core dependency footprint small; put optional dependencies behind extras in
  `pyproject.toml` and import them lazily.

## Common contributions

- **Add a connector** → [docs/connectors.md](docs/connectors.md).
- **Add a domain** → [docs/domain_packs.md](docs/domain_packs.md).
- **Add a source-config type** → [docs/sources.md](docs/sources.md).

## Commits & PRs

- Use conventional-commit-style messages (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`).
- Describe the *why*, not just the *what*.
- Reference related issues. Include a short test plan in the PR description.

## Code of conduct

By participating you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## License

By contributing, you agree your contributions are licensed under the project's
[Apache-2.0](LICENSE) license.
