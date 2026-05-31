"""Runnable demo — Retail (product).

Runs the full CanonIQ pipeline (profile -> suggest -> rules -> transform -> drift)
against the bundled synthetic data for this domain. Local-first: no network access.

    python examples/retail/demo.py
"""

from __future__ import annotations

import os

from canoniq import CanonIQ

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "source_products.csv")
NEW_SOURCE = os.path.join(HERE, "new_source_products.csv")
CANONICAL = os.path.join(HERE, "canonical_product.yml")


def main() -> None:
    engine = CanonIQ()

    # 1. Profile the source dataset.
    profile = engine.profile_source(SOURCE)

    # 2. Suggest source -> canonical mappings (scored + explained).
    mapping = engine.suggest_mappings(profile, CANONICAL)

    # 3. Generate validation rules from the canonical schema + profile.
    rules = engine.generate_validation_rules(mapping, CANONICAL, profile)

    # 4. Transform the source into canonical records (include review-tier maps).
    result = engine.apply_mapping(SOURCE, mapping, CANONICAL, include_review=True)

    # 5. Detect drift against a later ingestion.
    report = engine.detect_drift(NEW_SOURCE, mapping, CANONICAL)

    auto = sum(1 for m in mapping.mappings if m.status == "auto_approved")
    review = sum(1 for m in mapping.mappings if m.status == "requires_review")

    print("CanonIQ demo: Retail (product)")
    print(f"  profiled fields : {len(profile.fields)}")
    print(f"  mappings        : {auto} auto-approved, {review} need review")
    print(f"  validation rules: {len(rules)}")
    print(f"  canonical rows  : {len(result.records)}")
    print(f"  drift status    : {report.status}")
    print()
    print("  field mappings:")
    for m in mapping.mappings:
        target = m.canonical_field or "(unmapped)"
        why = ", ".join(m.reasons) if m.reasons else "-"
        print(f"    {m.source_field:>22} -> {target:<22} {m.confidence:.2f} {m.status}  [{why}]")


if __name__ == "__main__":
    main()
