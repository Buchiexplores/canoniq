"""Format validator unit tests, including checksum formats (§9, §14)."""

from __future__ import annotations

import pytest

from canoniq.validation.formats import (
    is_email,
    is_gtin,
    is_iban,
    is_iso3166_alpha2,
    is_iso4217,
    is_iso8601,
    is_lei,
    is_npi,
    is_uuid,
    validate_format,
)


@pytest.mark.parametrize("v,ok", [("a@b.com", True), ("nope", False), ("a@b", False)])
def test_email(v, ok):
    assert is_email(v) is ok


def test_uuid():
    assert is_uuid("123e4567-e89b-12d3-a456-426614174000")
    assert not is_uuid("not-a-uuid")


@pytest.mark.parametrize("v,ok", [
    ("2026-05-29", True),
    ("2026-05-29T09:14:00Z", True),
    ("2026-13-99", True),   # regex-level check (no calendar validation)
    ("29/05/2026", False),
])
def test_iso8601(v, ok):
    assert is_iso8601(v) is ok


@pytest.mark.parametrize("v,ok", [("US", True), ("us", True), ("USA", False)])
def test_iso3166_alpha2(v, ok):
    assert is_iso3166_alpha2(v) is ok


@pytest.mark.parametrize("v,ok", [("USD", True), ("eur", True), ("ZZZ", False)])
def test_iso4217(v, ok):
    assert is_iso4217(v) is ok


@pytest.mark.parametrize("v,ok", [
    ("GB82WEST12345698765432", True),
    ("DE89370400440532013000", True),
    ("GB00WEST12345698765432", False),  # bad checksum
])
def test_iban_checksum(v, ok):
    assert is_iban(v) is ok


@pytest.mark.parametrize("v,ok", [
    ("0123456789005", True),
    ("4006381333931", True),
    ("0123456789001", False),  # bad check digit
])
def test_gtin_checksum(v, ok):
    assert is_gtin(v) is ok


def test_npi_luhn():
    assert is_npi("1234567893") is True   # valid Luhn w/ 80840 prefix
    assert is_npi("1234567890") is False


def test_lei_mod97():
    # 20-char alnum; an invalid checksum must fail.
    assert is_lei("00000000000000000000") is False


def test_unknown_format_passes_gracefully():
    assert validate_format("not_a_real_format", "anything") is True
