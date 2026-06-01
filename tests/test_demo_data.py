"""Guard the bundled demo datasets.

``canoniq demo`` runs against data shipped *inside* the package
(``canoniq/demo_data/``) so it works from a plain ``pip install``. The richer,
human-readable copies live in the repo's ``examples/`` tree. These tests ensure the
packaged data exists, resolves, and stays byte-for-byte in sync with ``examples/``
so the two can never drift.
"""

from __future__ import annotations

import filecmp
import os

import pytest

from canoniq.demos.higher_ed import HIGHER_ED_CONFIG_DIR
from canoniq.domains import DOMAINS, demo_data_available, domain_paths


def test_demo_data_is_available():
    assert demo_data_available()


@pytest.mark.parametrize("domain", list(DOMAINS))
def test_domain_paths_resolve_to_real_files(domain: str):
    paths = domain_paths(domain)
    for key in ("canonical", "source", "new_source"):
        assert os.path.isfile(paths[key]), f"{domain}:{key} -> {paths[key]}"


@pytest.mark.parametrize("domain", list(DOMAINS))
def test_packaged_demo_data_matches_examples(domain: str, examples_dir: str):
    """Packaged demo data must equal the repo examples copy, byte-for-byte."""
    spec = DOMAINS[domain]
    example_base = os.path.join(examples_dir, spec["dir"])
    paths = domain_paths(domain)
    for key in ("canonical", "source", "new_source"):
        packaged = paths[key]
        original = os.path.join(example_base, spec[key])
        with open(packaged, "rb") as a, open(original, "rb") as b:
            assert a.read() == b.read(), f"{domain}:{key} drifted from examples/"


# --- bundled higher-ed onboarding walkthrough data (canoniq demo higher-ed) ---

_HE_PKG = os.path.dirname(HIGHER_ED_CONFIG_DIR)  # canoniq/demo_data/higher_ed_onboarding


def test_packaged_onboarding_configs_present():
    for school in ("northlake_university", "redwood_college", "pacific_state_university"):
        assert os.path.isfile(os.path.join(HIGHER_ED_CONFIG_DIR, f"{school}.yml"))


def test_packaged_onboarding_data_matches_example(examples_dir: str):
    """The packaged onboarding tree must equal the repo example tree, file-for-file."""
    example_root = os.path.join(examples_dir, "higher_ed_auto_onboarding")
    for sub in ("onboarding_configs", "canonical", "schools"):
        cmp = filecmp.dircmp(os.path.join(_HE_PKG, sub), os.path.join(example_root, sub))
        _assert_dirs_identical(cmp, sub)


def _assert_dirs_identical(cmp: filecmp.dircmp, where: str) -> None:
    assert not cmp.left_only, f"{where}: only in package: {cmp.left_only}"
    assert not cmp.right_only, f"{where}: only in example: {cmp.right_only}"
    assert not cmp.diff_files, f"{where}: differing files: {cmp.diff_files}"
    for name, sub in cmp.subdirs.items():
        _assert_dirs_identical(sub, f"{where}/{name}")
