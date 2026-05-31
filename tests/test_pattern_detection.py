"""Pattern detection unit tests (§12.1)."""

from __future__ import annotations

from canoniq.core import constants as C
from canoniq.profiler.pattern_detection import detect_patterns


def _detect(values, **kw):
    defaults = dict(
        null_rate=0.0, unique_rate=1.0, numeric_min=None, numeric_max=None, distinct_count=None
    )
    defaults.update(kw)
    return detect_patterns(values, **defaults)


def test_email_pattern():
    pats = _detect(["a@x.com", "b@y.org", "c@z.net"])
    assert C.PATTERN_EMAIL in pats


def test_gtin_pattern():
    pats = _detect(["0123456789005", "4006381333931", "8859092101070"])
    assert C.PATTERN_GTIN_LIKE in pats


def test_range_0_to_4_for_gpa():
    pats = _detect(["3.5", "2.9", "4.0"], numeric_min=2.9, numeric_max=4.0)
    assert C.PATTERN_RANGE_0_4 in pats
    assert C.PATTERN_POSITIVE_NUMBER in pats


def test_mostly_unique_pattern():
    pats = _detect(["a", "b", "c"], unique_rate=0.95)
    assert C.PATTERN_MOSTLY_UNIQUE in pats


def test_enum_like_pattern():
    pats = _detect(["x", "y"], unique_rate=0.2, distinct_count=2)
    assert C.PATTERN_ENUM_LIKE in pats


def test_high_null_rate_pattern():
    pats = _detect(["a", "b"], null_rate=0.8)
    assert C.PATTERN_HIGH_NULL_RATE in pats


def test_currency_code_pattern():
    pats = _detect(["USD", "EUR", "GBP"])
    assert C.PATTERN_CURRENCY_CODE_LIKE in pats
