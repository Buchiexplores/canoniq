"""Domain helpers: locate the bundled demo datasets.

Domain behavior comes entirely from canonical-schema YAML — there is no per-domain
code in the engine. These helpers only resolve paths to the demo data the ``demo``
command runs against.

The demo datasets are **shipped inside the package** (``canoniq/demo_data/``) so
``canoniq demo`` works from a plain ``pip install`` — not only from a source
checkout. The richer, human-readable copies live in the repo's ``examples/`` tree;
a test keeps the two byte-for-byte in sync.
"""

from __future__ import annotations

import os

# Demo datasets shipped with the package (works after `pip install canoniq`).
_DEMO_DATA_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "demo_data"))

# repo-root/examples (present only in a source checkout; used by example/onboarding tests).
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

# STAR narrative shown by ``canoniq demo`` so each run reads as a use case
# (Situation / Task / Action / Result), not just a table. Kept concise for the
# terminal; the full write-ups live in docs/demos.md.
DEMO_STAR: dict[str, dict[str, str]] = {
    "higher-ed": {
        "situation": (
            "A university powers an advising dashboard from a Banner SIS export with "
            "institution-specific headers (banner_id, cumulative_gpa, last_activity_at)."
        ),
        "task": (
            "Map the export onto the canonical 'student' model, validate it, and stay "
            "resilient to next term's column changes."
        ),
        "value": (
            "A new school's data is dashboard-ready in seconds; schema changes surface as "
            "a review item, not a broken report."
        ),
    },
    "retail": {
        "situation": (
            "A marketplace lists products from many suppliers, each with its own feed "
            "(sku_id, sale_price, available_qty) and no shared currency contract."
        ),
        "task": (
            "Normalize a supplier catalog onto the canonical 'product' model so items "
            "list and price consistently."
        ),
        "value": (
            "The 500th supplier onboards as easily as the 1st; a renamed column doesn't "
            "silently break pricing."
        ),
    },
    "healthcare": {
        "situation": (
            "A clinic integrates an EHR patient extract with terse headers (mrn, dob, "
            "icd10_code) and sensitive identifiers."
        ),
        "task": (
            "Map onto a FHIR-aligned 'patient' model, validate codes and formats, and "
            "keep PHI masked by default."
        ),
        "value": (
            "Partner feeds align to one model, sensitive values are masked, and a "
            "coding-system swap (ICD-10 to SNOMED) is caught, not absorbed."
        ),
    },
    "finance": {
        "situation": (
            "A fintech ingests a partner bank's daily transaction file with abbreviated "
            "headers (txn_id, iban, drcr, txn_amt)."
        ),
        "task": (
            "Reconcile onto an ISO 20022-aligned 'transaction' model with IBAN, currency, "
            "and timestamp checks."
        ),
        "value": (
            "Clean, standards-backed reconciliation that survives the bank silently "
            "reformatting its feed."
        ),
    },
    "logistics": {
        "situation": (
            "A 3PL aggregates shipment feeds from many carriers with varying, sometimes "
            "ambiguous names (shipment_no, from_zip, eta)."
        ),
        "task": (
            "Unify a carrier feed onto the canonical 'shipment' model and surface anything "
            "too uncertain to auto-map."
        ),
        "value": (
            "Confident mappings flow through; ambiguous ones are escalated for review "
            "instead of guessed."
        ),
    },
}


def examples_dir() -> str:
    return _EXAMPLES_DIR


def examples_available() -> bool:
    """True when the repo's ``examples/`` tree is reachable (source checkout only)."""
    return os.path.isdir(_EXAMPLES_DIR)


def demo_data_available() -> bool:
    """True when the packaged demo datasets are present (always so once installed)."""
    return os.path.isdir(_DEMO_DATA_DIR)


def domain_paths(domain: str) -> dict[str, str]:
    if domain not in DOMAINS:
        raise KeyError(f"Unknown demo domain {domain!r}. Known: {', '.join(DOMAINS)}.")
    if not demo_data_available():
        raise FileNotFoundError(
            f"Bundled demo datasets were not found (expected at {_DEMO_DATA_DIR!r}). "
            "This usually means a broken install — reinstall with `pip install --force-reinstall "
            "canoniq`, or clone the repo: https://github.com/Buchiexplores/canoniq"
        )
    spec = DOMAINS[domain]
    base = os.path.join(_DEMO_DATA_DIR, spec["dir"])
    return {
        "canonical": os.path.join(base, spec["canonical"]),
        "source": os.path.join(base, spec["source"]),
        "new_source": os.path.join(base, spec["new_source"]),
        "entity": spec["entity"],
        "base": base,
    }


__all__ = [
    "DOMAINS",
    "DEMO_STAR",
    "examples_dir",
    "examples_available",
    "demo_data_available",
    "domain_paths",
]
