"""Config loading/overrides and mapping registry round-trip tests."""

from __future__ import annotations

import pytest

from canoniq.config import CanonIQConfig
from canoniq.core.models import MappingResult, MappingSuggestion
from canoniq.registry import load_mapping, save_mapping


def test_default_config():
    cfg = CanonIQConfig()
    assert cfg.auto_approve_threshold == 0.90
    assert cfg.review_threshold == 0.70
    assert cfg.mask_pii is True
    assert abs(sum(v for k, v in cfg.weights.items() if k != "semantic") - 1.0) < 1e-9


def test_config_from_yaml(tmp_path):
    p = tmp_path / "cfg.yml"
    p.write_text("auto_approve_threshold: 0.95\nmask_pii: false\n")
    cfg = CanonIQConfig.from_yaml(str(p))
    assert cfg.auto_approve_threshold == 0.95
    assert cfg.mask_pii is False


def test_config_from_yaml_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        CanonIQConfig.from_yaml(str(tmp_path / "nope.yml"))


def test_with_overrides_ignores_none():
    base = CanonIQConfig()
    overridden = base.with_overrides(auto_approve_threshold=0.8, review_threshold=None)
    assert overridden.auto_approve_threshold == 0.8
    assert overridden.review_threshold == base.review_threshold


def test_mapping_round_trip(tmp_path):
    result = MappingResult(
        canonical={"domain": "d", "entity": "e", "version": 1},
        mappings=[
            MappingSuggestion(
                source_field="a", canonical_field="x", confidence=0.91,
                status="auto_approved", reasons=["alias match"], signals={"alias": 1.0},
            ),
        ],
        canoniq_version="0.1.0",
    )
    path = tmp_path / "m.json"
    save_mapping(result, str(path))
    loaded = load_mapping(str(path))
    assert loaded.canonical == result.canonical
    assert loaded.mappings[0].source_field == "a"
    assert loaded.mappings[0].confidence == 0.91


def test_load_mapping_missing_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_mapping(str(tmp_path / "nope.json"))
