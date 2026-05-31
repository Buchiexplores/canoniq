"""Source-config loading + ${ENV} interpolation + secret-warning tests (§19)."""

from __future__ import annotations

import logging

import pytest

from canoniq.sources import build_connector, load_source_config
from canoniq.sources.config_loader import SourceConfigError


def test_loads_local_csv_config(tmp_path):
    cfg = tmp_path / "src.yml"
    cfg.write_text("source:\n  type: csv\n  path: data.csv\n  sample_limit: 100\n")
    src = load_source_config(str(cfg))
    assert src["type"] == "csv"
    assert src["path"] == "data.csv"
    assert src["sample_limit"] == 100


def test_env_interpolation(tmp_path, monkeypatch):
    monkeypatch.setenv("PGHOST", "db.internal")
    cfg = tmp_path / "src.yml"
    cfg.write_text("source:\n  type: postgres\n  host: ${PGHOST}\n  table: t\n")
    src = load_source_config(str(cfg))
    assert src["host"] == "db.internal"


def test_missing_env_var_raises(tmp_path):
    cfg = tmp_path / "src.yml"
    cfg.write_text("source:\n  type: postgres\n  host: ${DEFINITELY_UNSET_VAR_XYZ}\n  table: t\n")
    with pytest.raises(SourceConfigError):
        load_source_config(str(cfg))


def test_inline_secret_warning(tmp_path, caplog):
    cfg = tmp_path / "src.yml"
    cfg.write_text("source:\n  type: postgres\n  password: hunter2\n  table: t\n")
    with caplog.at_level(logging.WARNING, logger="canoniq.sources"):
        load_source_config(str(cfg))
    assert any("inline secret" in r.message for r in caplog.records)


def test_no_warning_when_secret_uses_env(tmp_path, caplog, monkeypatch):
    monkeypatch.setenv("PGPASS", "s3cr3t")
    cfg = tmp_path / "src.yml"
    cfg.write_text("source:\n  type: postgres\n  password: ${PGPASS}\n  table: t\n")
    with caplog.at_level(logging.WARNING, logger="canoniq.sources"):
        load_source_config(str(cfg))
    assert not any("inline secret" in r.message for r in caplog.records)


def test_missing_top_level_source_key_raises(tmp_path):
    cfg = tmp_path / "src.yml"
    cfg.write_text("not_source:\n  type: csv\n")
    with pytest.raises(SourceConfigError):
        load_source_config(str(cfg))


def test_build_connector_for_csv(tmp_path):
    cfg = tmp_path / "src.yml"
    cfg.write_text("source:\n  type: csv\n  path: data.csv\n")
    conn, resolved = build_connector(load_source_config(str(cfg)))
    assert type(conn).__name__ == "CSVConnector"
    assert resolved["type"] == "csv"
