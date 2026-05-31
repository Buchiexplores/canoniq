"""Persist and load mapping results as JSON (§20 contract)."""

from __future__ import annotations

import json
import os

from canoniq.core.models import MappingResult


def save_mapping(result: MappingResult, path: str) -> None:
    """Write a ``MappingResult`` to a JSON file (stable shape)."""
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(result.model_dump(), fh, indent=2, sort_keys=False)
        fh.write("\n")


def load_mapping(path: str) -> MappingResult:
    """Load a ``MappingResult`` from a JSON file written by :func:`save_mapping`."""
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Mapping file not found: {path}")
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return MappingResult.model_validate(data)
