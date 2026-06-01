"""Guard the bundled demo datasets.

``canoniq demo`` runs against data shipped *inside* the package
(``canoniq/demo_data/``) so it works from a plain ``pip install``. The richer,
human-readable copies live in the repo's ``examples/`` tree. These tests ensure the
packaged data exists, resolves, and stays byte-for-byte in sync with ``examples/``
so the two can never drift.
"""

from __future__ import annotations

import os

import pytest

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
