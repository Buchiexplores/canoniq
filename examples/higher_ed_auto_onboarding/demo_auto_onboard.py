#!/usr/bin/env python3
"""CampusLaunch AI — comprehensive auto-onboarding demonstration.

A presentation-grade walkthrough of how CanonIQ auto-onboards multiple universities
into a shared canonical model. This is a thin wrapper over the packaged renderer
(``canoniq.demos.higher_ed.run_campuslaunch_demo``) pointed at this example's own
config directory — the same walkthrough you get from ``canoniq demo higher-ed``.

Run it (no arguments, no network)::

    python examples/higher_ed_auto_onboarding/demo_auto_onboard.py

Equivalent CLI::

    canoniq demo higher-ed
"""

from __future__ import annotations

import os

from canoniq import __version__
from canoniq.demos.higher_ed import run_campuslaunch_demo

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(HERE, "onboarding_configs")
OUTPUT_DIR = os.path.join(HERE, "output")


def main() -> None:
    run_campuslaunch_demo(config_dir=CONFIG_DIR, out_dir=OUTPUT_DIR, version=__version__)


if __name__ == "__main__":
    main()
