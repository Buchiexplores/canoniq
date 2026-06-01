"""Packaged, presentation-grade demonstrations.

These render rich, narrated walkthroughs of CanonIQ against bundled synthetic data
so they work straight from a ``pip install`` (no source checkout). Currently the
flagship is the higher-education *CampusLaunch AI* multi-school auto-onboarding
walkthrough surfaced by ``canoniq demo higher-ed``.
"""

from __future__ import annotations

from canoniq.demos.higher_ed import HIGHER_ED_CONFIG_DIR, run_campuslaunch_demo

__all__ = ["run_campuslaunch_demo", "HIGHER_ED_CONFIG_DIR"]
