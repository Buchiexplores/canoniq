"""Type inference unit tests (§11.2)."""

from __future__ import annotations

import pytest

from canoniq.profiler.type_inference import infer_column_type, infer_value_type


@pytest.mark.parametrize(
    "value,expected",
    [
        ("user@example.com", "email"),
        ("USD", "currency_code"),
        ("12.5%", "percentage"),
        ("42", "integer"),
        ("-7", "integer"),
        ("3.14", "decimal"),
        ("true", "boolean"),
        ("2026-05-29", "date"),
        ("2026-05-29T09:14:00Z", "timestamp"),
        ('{"a": 1}', "json"),
        ("[1, 2, 3]", "array"),
        ("hello world", "string"),
        ("", "unknown"),
    ],
)
def test_infer_value_type(value, expected):
    assert infer_value_type(value) == expected


def test_integer_only_column_stays_integer():
    assert infer_column_type(["1", "2", "3", "100"]) == "integer"


def test_int_decimal_mix_becomes_decimal():
    assert infer_column_type(["1", "2.5", "3"]) == "decimal"


def test_word_booleans_become_boolean():
    assert infer_column_type(["yes", "no", "yes"]) == "boolean"


def test_zero_one_stays_integer_not_boolean():
    assert infer_column_type(["0", "1", "1", "0"]) == "integer"


def test_long_strings_become_text():
    long = "x" * 80
    assert infer_column_type([long, long, long]) == "text"


def test_empty_column_is_unknown():
    assert infer_column_type(["", "", None]) == "unknown"
