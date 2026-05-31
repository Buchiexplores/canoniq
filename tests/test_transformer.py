"""Transformation tests: rename, drop unmapped, type coercion (§15)."""

from __future__ import annotations

import os

from canoniq.connectors import CSVConnector
from canoniq.matcher.mapping_engine import MappingEngine
from canoniq.profiler import Profiler
from canoniq.registry import load_canonical_schema
from canoniq.transform import apply_mapping


def _retail_setup(examples_dir):
    base = os.path.join(examples_dir, "retail")
    conn = CSVConnector(os.path.join(base, "source_products.csv"))
    records = conn.sample()
    profile = Profiler().profile(records, conn.get_metadata())
    schema = load_canonical_schema(os.path.join(base, "canonical_product.yml"))
    mapping = MappingEngine().suggest(profile, schema)
    return records, schema, mapping


def test_columns_renamed_to_canonical(examples_dir):
    records, schema, mapping = _retail_setup(examples_dir)
    result = apply_mapping(records, mapping, schema, include_review=True)
    assert "price" in result.columns
    assert "sale_price" not in result.columns


def test_output_column_order_follows_schema(examples_dir):
    records, schema, mapping = _retail_setup(examples_dir)
    result = apply_mapping(records, mapping, schema, include_review=True)
    schema_order = [n for n in schema.fields if n in result.columns]
    assert result.columns[: len(schema_order)] == schema_order


def test_unmapped_dropped_by_default(examples_dir):
    records, schema, mapping = _retail_setup(examples_dir)
    result = apply_mapping(records, mapping, schema, include_review=True)
    mapped_canonical = set(mapping.approved_mappings(include_review=True).values())
    assert set(result.columns) == mapped_canonical


def test_keep_unmapped_retains_extra_columns():
    from canoniq.core.models import MappingResult, MappingSuggestion

    mapping = MappingResult(
        canonical={"domain": "d", "entity": "e", "version": 1},
        mappings=[
            MappingSuggestion(source_field="a", canonical_field="x", confidence=1.0, status="auto_approved"),
        ],
    )
    records = [{"a": "1", "extra": "keep"}]
    result = apply_mapping(records, mapping, schema=None, keep_unmapped=True)
    assert "x" in result.columns
    assert "extra" in result.columns


def test_decimal_and_integer_coercion(examples_dir):
    records, schema, mapping = _retail_setup(examples_dir)
    result = apply_mapping(records, mapping, schema, include_review=True)
    row = result.records[0]
    assert isinstance(row["price"], float)
    assert isinstance(row["inventory_quantity"], int)


def test_coercion_error_recorded_not_swallowed():
    from canoniq.core.models import (
        CanonicalEntity,
        CanonicalField,
        MappingResult,
        MappingSuggestion,
    )

    schema = CanonicalEntity(
        domain="d", entity="e", version=1, primary_key=["x"],
        fields={"x": CanonicalField(name="x", type="boolean")},
    )
    mapping = MappingResult(
        canonical={"domain": "d", "entity": "e", "version": 1},
        mappings=[MappingSuggestion(source_field="a", canonical_field="x", confidence=1.0, status="auto_approved")],
    )
    result = apply_mapping([{"a": "definitely-not-bool"}], mapping, schema)
    assert len(result.coercion_errors) == 1
    assert result.coercion_errors[0]["field"] == "x"
