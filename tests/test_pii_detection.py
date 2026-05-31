"""PII/PHI detection + masking unit tests (§12.2)."""

from __future__ import annotations

from canoniq.profiler.pii_detection import detect_pii_flags, mask_value, should_mask


def test_detects_email_by_name():
    assert "email" in detect_pii_flags("student_email", ["a@x.com"])


def test_detects_email_by_value_only():
    flags = detect_pii_flags("contact", ["a@x.com", "b@y.org"])
    assert "email" in flags


def test_detects_name_field():
    assert "name" in detect_pii_flags("first_name", ["Jordan"])


def test_detects_mrn_as_high_pii():
    flags = detect_pii_flags("mrn", ["MRN0001001"])
    assert "mrn" in flags
    assert should_mask(flags) is True


def test_detects_ssn_by_value():
    flags = detect_pii_flags("identifier", ["123-45-6789"])
    assert "national_id" in flags


def test_mask_email():
    assert mask_value("jordan.lee@example.edu", ["email"]) == "j***@***"


def test_mask_numeric_high_pii():
    masked = mask_value("123456789", ["national_id"])
    assert masked.startswith("1")
    assert set(masked[1:]) == {"*"}


def test_should_not_mask_when_no_flags():
    assert should_mask([]) is False
