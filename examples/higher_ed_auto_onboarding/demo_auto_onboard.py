#!/usr/bin/env python3
"""CampusLaunch AI — auto-onboarding demo.

Runs CanonIQ's config-driven onboarding over three fictional schools and prints a
deployment-readiness verdict for each, plus a combined roll-up. Nothing is
deployed: the output is a readiness score and the canonical artifacts a deploy
step *could* consume.

Higher education is just one illustration — each school is modeled as a generic
"provider", the same provider-neutral abstraction CanonIQ uses for retail vendors,
hospitals, SaaS tenants, and any other source of data.

Run it (no arguments needed)::

    python examples/higher_ed_auto_onboarding/demo_auto_onboard.py

Equivalent CLI::

    canoniq onboard-batch \
        --config-dir examples/higher_ed_auto_onboarding/onboarding_configs \
        --combined-out examples/higher_ed_auto_onboarding/output/combined_readiness.json
"""

from __future__ import annotations

import os

from canoniq import __version__
from canoniq.onboarding import onboard_providers

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(HERE, "onboarding_configs")
COMBINED_OUT = os.path.join(HERE, "output", "combined_readiness.json")


def main() -> None:
    reports, combined = onboard_providers(
        CONFIG_DIR,
        write_outputs=True,
        combined_out=COMBINED_OUT,
        canoniq_version=__version__,
    )

    for report in reports:
        print(f"\n=== {report.provider_name} ({report.provider_id}) ===")
        print(f"  readiness score : {report.readiness_score}")
        print(f"  status          : {report.status}")
        print(f"  auto-deploy     : {report.auto_deploy_allowed}")
        s = report.summary
        print(f"  fields mapped   : {s.mapped_fields}/{s.total_fields}")
        print(f"  auto-approved   : {s.auto_approved_mappings}  needs-review: {s.requires_review}")
        print(f"  required covered: {s.required_fields_covered}")
        print(f"  next action     : {report.next_action}")
        print("  component scores:")
        for name, comp in report.component_scores.items():
            print(f"    - {name:<16} ratio={comp.ratio:.2f} points={comp.points}")

    print("\n=== Combined ===")
    print(f"  total providers        : {combined.total_providers}")
    print(f"  ready_for_auto_deploy  : {combined.ready_for_auto_deploy}")
    print(f"  ready_with_minor_review: {combined.ready_with_minor_review}")
    print(f"  needs_mapping_review   : {combined.needs_mapping_review}")
    print(f"  blocked                : {combined.blocked}")
    print(f"\nWrote per-provider reports to output/ and combined summary to:\n  {COMBINED_OUT}")


if __name__ == "__main__":
    main()
