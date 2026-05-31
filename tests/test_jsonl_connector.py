"""JSONL connector tests."""

from __future__ import annotations

import json

import pytest

from canoniq.connectors import JSONLConnector


def _write_jsonl(path, rows):
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")


def test_jsonl_reads_one_object_per_line(tmp_path):
    p = tmp_path / "data.jsonl"
    _write_jsonl(p, [{"id": "1", "v": "a"}, {"id": "2", "v": "b"}, {"id": "3", "v": "c"}])
    conn = JSONLConnector(str(p))
    rows = conn.sample()
    assert [r["id"] for r in rows] == ["1", "2", "3"]


def test_jsonl_skips_blank_lines_and_respects_limit(tmp_path):
    p = tmp_path / "data.jsonl"
    p.write_text('{"id": "1"}\n\n{"id": "2"}\n{"id": "3"}\n')
    conn = JSONLConnector(str(p))
    assert len(conn.sample()) == 3
    assert len(conn.sample(limit=2)) == 2


def test_jsonl_missing_file_raises(tmp_path):
    conn = JSONLConnector(str(tmp_path / "missing.jsonl"))
    with pytest.raises(FileNotFoundError):
        conn.sample()
