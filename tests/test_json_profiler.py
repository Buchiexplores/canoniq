"""JSON connector + profiler tests."""

from __future__ import annotations

import json
import os

from canoniq.connectors import JSONConnector
from canoniq.profiler import Profiler


def test_json_connector_reads_wrapped_records(examples_dir):
    path = os.path.join(examples_dir, "retail", "source_products.json")
    conn = JSONConnector(path)
    rows = conn.sample(limit=1000)
    assert len(rows) == 7
    assert rows[0]["sku_id"] == "0123456789005"


def test_json_connector_reads_bare_array(tmp_path):
    path = tmp_path / "data.json"
    path.write_text(json.dumps([{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]))
    conn = JSONConnector(str(path))
    rows = conn.sample()
    assert len(rows) == 2
    assert rows[1]["b"] == "y"


def test_profiler_on_json(examples_dir):
    path = os.path.join(examples_dir, "retail", "source_products.json")
    conn = JSONConnector(path)
    profile = Profiler().profile(conn.sample(), conn.get_metadata())
    by_name = {f.name: f for f in profile.fields}
    assert by_name["sale_price"].inferred_type == "decimal"
    assert by_name["available_qty"].inferred_type == "integer"
    assert by_name["currency"].inferred_type == "currency_code"
