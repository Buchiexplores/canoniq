"""CLI tests via Typer's CliRunner (§21). Exercises the full command surface."""

from __future__ import annotations

import json
import os

from typer.testing import CliRunner

from canoniq import __version__
from canoniq.cli import app

runner = CliRunner()


def _he(examples_dir, name):
    return os.path.join(examples_dir, "higher_ed", name)


def test_version():
    res = runner.invoke(app, ["version"])
    assert res.exit_code == 0
    assert __version__ in res.stdout


def test_profile_command(examples_dir, tmp_path):
    out = tmp_path / "profile.json"
    res = runner.invoke(app, [
        "profile", "--source", _he(examples_dir, "source_students.csv"),
        "--out", str(out),
    ])
    assert res.exit_code == 0
    data = json.loads(out.read_text())
    assert data["row_count_sampled"] == 10
    assert data["fields"]


def test_profile_requires_a_source():
    res = runner.invoke(app, ["profile"])
    assert res.exit_code != 0


def test_profile_rejects_both_inputs(examples_dir, tmp_path):
    res = runner.invoke(app, [
        "profile",
        "--source", _he(examples_dir, "source_students.csv"),
        "--source-config", "whatever.yml",
        "--out", str(tmp_path / "p.json"),
    ])
    assert res.exit_code != 0


def test_full_cli_pipeline(examples_dir, tmp_path):
    profile_json = tmp_path / "profile.json"
    suggestions_json = tmp_path / "suggestions.json"
    rules_yml = tmp_path / "rules.yml"
    output_csv = tmp_path / "out.csv"
    drift_json = tmp_path / "drift.json"
    canonical = _he(examples_dir, "canonical_student.yml")

    r1 = runner.invoke(app, [
        "profile", "--source", _he(examples_dir, "source_students.csv"),
        "--out", str(profile_json),
    ])
    assert r1.exit_code == 0

    r2 = runner.invoke(app, [
        "suggest", "--profile", str(profile_json),
        "--canonical", canonical, "--out", str(suggestions_json),
    ])
    assert r2.exit_code == 0
    assert suggestions_json.exists()

    r3 = runner.invoke(app, [
        "rules", "--suggestions", str(suggestions_json),
        "--canonical", canonical, "--out", str(rules_yml),
    ])
    assert r3.exit_code == 0
    assert rules_yml.exists()

    r4 = runner.invoke(app, [
        "apply", "--source", _he(examples_dir, "source_students.csv"),
        "--mapping", str(suggestions_json), "--canonical", canonical,
        "--out", str(output_csv), "--include-review",
    ])
    assert r4.exit_code == 0
    assert output_csv.exists()

    r5 = runner.invoke(app, [
        "drift-check", "--source", _he(examples_dir, "new_source_students.csv"),
        "--mapping", str(suggestions_json), "--canonical", canonical,
        "--out", str(drift_json),
    ])
    assert r5.exit_code == 0
    report = json.loads(drift_json.read_text())
    assert report["status"] == "drift_detected"


def test_demo_command(tmp_path):
    res = runner.invoke(app, ["demo", "retail", "--out-dir", str(tmp_path)])
    assert res.exit_code == 0
    assert (tmp_path / "product" / "suggestions.json").exists()
    assert (tmp_path / "product" / "drift_report.json").exists()


def test_demo_unknown_domain():
    res = runner.invoke(app, ["demo", "not_a_domain"])
    assert res.exit_code == 1


def test_profile_bad_source_exits_nonzero(tmp_path):
    res = runner.invoke(app, [
        "profile", "--source", str(tmp_path / "missing.csv"),
        "--out", str(tmp_path / "p.json"),
    ])
    assert res.exit_code == 1


def test_demo_accepts_config_file(tmp_path):
    cfg = tmp_path / "canoniq.yml"
    cfg.write_text("auto_approve_threshold: 0.95\nreview_threshold: 0.60\n")
    res = runner.invoke(app, [
        "demo", "retail", "--out-dir", str(tmp_path), "--config", str(cfg),
    ])
    assert res.exit_code == 0
    assert (tmp_path / "product" / "suggestions.json").exists()


def test_config_missing_file_exits_nonzero(tmp_path):
    res = runner.invoke(app, [
        "demo", "retail", "--out-dir", str(tmp_path),
        "--config", str(tmp_path / "nope.yml"),
    ])
    assert res.exit_code != 0
