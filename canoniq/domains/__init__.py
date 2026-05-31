"""Domain helpers: locate bundled example canonical schemas.

Domain behavior comes entirely from canonical-schema YAML — there is no per-domain
code in the engine. These helpers only resolve paths to the bundled examples so the
``demo`` command and tests can find them.
"""

from __future__ import annotations

import os

# repo-root/examples
_EXAMPLES_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "examples")
)

# domain key -> (subdir, canonical filename, source filename, new_source filename, entity)
DOMAINS: dict[str, dict[str, str]] = {
    "higher-ed": {
        "dir": "higher_ed",
        "canonical": "canonical_student.yml",
        "source": "source_students.csv",
        "new_source": "new_source_students.csv",
        "entity": "student",
    },
    "retail": {
        "dir": "retail",
        "canonical": "canonical_product.yml",
        "source": "source_products.csv",
        "new_source": "new_source_products.csv",
        "entity": "product",
    },
    "healthcare": {
        "dir": "healthcare",
        "canonical": "canonical_patient.yml",
        "source": "source_patients.csv",
        "new_source": "new_source_patients.csv",
        "entity": "patient",
    },
    "finance": {
        "dir": "finance",
        "canonical": "canonical_transaction.yml",
        "source": "source_transactions.csv",
        "new_source": "new_source_transactions.csv",
        "entity": "transaction",
    },
    "logistics": {
        "dir": "logistics",
        "canonical": "canonical_shipment.yml",
        "source": "source_shipments.csv",
        "new_source": "new_source_shipments.csv",
        "entity": "shipment",
    },
}


def examples_dir() -> str:
    return _EXAMPLES_DIR


def domain_paths(domain: str) -> dict[str, str]:
    if domain not in DOMAINS:
        raise KeyError(f"Unknown demo domain {domain!r}. Known: {', '.join(DOMAINS)}.")
    spec = DOMAINS[domain]
    base = os.path.join(_EXAMPLES_DIR, spec["dir"])
    return {
        "canonical": os.path.join(base, spec["canonical"]),
        "source": os.path.join(base, spec["source"]),
        "new_source": os.path.join(base, spec["new_source"]),
        "entity": spec["entity"],
        "base": base,
    }
