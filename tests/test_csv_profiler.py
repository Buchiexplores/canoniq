"""CSV connector + profiler integration tests."""

from __future__ import annotations

import os

import pytest

from canoniq.connectors import CSVConnector
from canoniq.profiler import Profiler


def _students_csv(examples_dir: str) -> str:
    return os.path.join(examples_dir, "higher_ed", "source_students.csv")


def test_csv_connector_reads_rows(examples_dir):
    conn = CSVConnector(_students_csv(examples_dir))
    assert conn.test_connection() is True
    rows = conn.sample(limit=1000)
    assert len(rows) == 10
    assert rows[0]["banner_id"] == "B00010234"
    assert set(rows[0].keys()) == {
        "banner_id", "student_email", "first_name", "last_name",
        "cumulative_gpa", "status", "last_activity_at",
    }


def test_csv_connector_respects_limit(examples_dir):
    conn = CSVConnector(_students_csv(examples_dir))
    assert len(conn.sample(limit=3)) == 3


def test_csv_connector_missing_file_raises(tmp_path):
    conn = CSVConnector(str(tmp_path / "nope.csv"))
    assert conn.test_connection() is False
    with pytest.raises(FileNotFoundError):
        conn.sample()


def test_profiler_preserves_column_order_and_types(examples_dir):
    conn = CSVConnector(_students_csv(examples_dir))
    profile = Profiler().profile(conn.sample(), conn.get_metadata())

    assert profile.row_count_sampled == 10
    names = [f.name for f in profile.fields]
    assert names[0] == "banner_id"  # first-seen order preserved
    assert names == [
        "banner_id", "student_email", "first_name", "last_name",
        "cumulative_gpa", "status", "last_activity_at",
    ]

    by_name = {f.name: f for f in profile.fields}
    assert by_name["banner_id"].inferred_type == "string"
    assert by_name["student_email"].inferred_type == "email"
    assert by_name["cumulative_gpa"].inferred_type == "decimal"
    assert by_name["last_activity_at"].inferred_type == "timestamp"


def test_profiler_masks_email_sample_values(examples_dir):
    conn = CSVConnector(_students_csv(examples_dir))
    profile = Profiler(mask_pii=True).profile(conn.sample(), conn.get_metadata())
    email = profile.field("student_email")
    assert email is not None
    assert "email" in email.pii_flags
    # raw addresses must never appear; masked form is a***@***
    for sv in email.sample_values:
        assert "@example.edu" not in sv
        assert sv.endswith("@***")


def test_profiler_numeric_stats(examples_dir):
    conn = CSVConnector(_students_csv(examples_dir))
    profile = Profiler().profile(conn.sample(), conn.get_metadata())
    gpa = profile.field("cumulative_gpa")
    assert gpa is not None
    assert gpa.min is not None and gpa.max is not None
    assert 0.0 <= gpa.min <= gpa.max <= 4.0
