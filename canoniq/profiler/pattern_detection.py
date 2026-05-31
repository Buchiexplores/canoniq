"""Pattern detection over sampled values (§12.1)."""

from __future__ import annotations

import re

from canoniq.core import constants as C
from canoniq.profiler.type_inference import (
    DATE_RES,
    DATETIME_RES,
    DECIMAL_RE,
    EMAIL_RE,
    INT_RE,
)

UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_\-]{2,}$")
CURRENCY_AMOUNT_RE = re.compile(r"^[\$€£¥]\s?\d")
IBAN_RE = re.compile(r"^[A-Z]{2}\d{2}[A-Z0-9]{10,30}$")
GTIN_RE = re.compile(r"^\d{8}$|^\d{12,14}$")
POSTAL_RE = re.compile(r"^\d{5}(-\d{4})?$|^[A-Za-z]\d[A-Za-z]\s?\d[A-Za-z]\d$")
PHONE_RE = re.compile(r"^\+?[\d\s().\-]{7,}$")
COUNTRY_CODE_RE = re.compile(r"^[A-Za-z]{2}$")


def _ratio(values: list[str], predicate) -> float:
    if not values:
        return 0.0
    hits = sum(1 for v in values if predicate(v))
    return hits / len(values)


def detect_patterns(
    values: list[str],
    *,
    null_rate: float,
    unique_rate: float,
    numeric_min: float | None,
    numeric_max: float | None,
    distinct_count: int | None,
) -> list[str]:
    """Return the list of patterns matched by a column's sampled values."""
    non_empty = [str(v).strip() for v in values if v is not None and str(v).strip() != ""]
    patterns: list[str] = []

    def maybe(name: str, ratio: float, threshold: float = 0.9) -> None:
        if ratio >= threshold:
            patterns.append(name)

    if non_empty:
        maybe(C.PATTERN_EMAIL, _ratio(non_empty, lambda v: bool(EMAIL_RE.match(v))))
        maybe(C.PATTERN_UUID_LIKE, _ratio(non_empty, lambda v: bool(UUID_RE.match(v))))
        maybe(C.PATTERN_INTEGER, _ratio(non_empty, lambda v: bool(INT_RE.match(v))))
        maybe(
            C.PATTERN_DECIMAL,
            _ratio(non_empty, lambda v: bool(DECIMAL_RE.match(v)) and "." in v),
        )
        maybe(
            C.PATTERN_TIMESTAMP_ISO,
            _ratio(non_empty, lambda v: any(rx.match(v) for rx in DATETIME_RES)),
        )
        maybe(
            C.PATTERN_DATE,
            _ratio(non_empty, lambda v: any(rx.match(v) for rx in DATE_RES)),
        )
        maybe(C.PATTERN_CURRENCY_LIKE, _ratio(non_empty, lambda v: bool(CURRENCY_AMOUNT_RE.match(v))))
        maybe(
            C.PATTERN_CURRENCY_CODE_LIKE,
            _ratio(non_empty, lambda v: len(v) == 3 and v.isalpha() and v.upper() in C.CURRENCY_CODES),
        )
        maybe(C.PATTERN_IBAN_LIKE, _ratio(non_empty, lambda v: bool(IBAN_RE.match(v.replace(" ", "")))))
        maybe(C.PATTERN_GTIN_LIKE, _ratio(non_empty, lambda v: bool(GTIN_RE.match(v))))
        maybe(C.PATTERN_POSTAL_CODE_LIKE, _ratio(non_empty, lambda v: bool(POSTAL_RE.match(v))))
        maybe(C.PATTERN_PHONE_LIKE, _ratio(non_empty, lambda v: bool(PHONE_RE.match(v)) and any(c.isdigit() for c in v)))
        maybe(
            C.PATTERN_COUNTRY_CODE_LIKE,
            _ratio(non_empty, lambda v: bool(COUNTRY_CODE_RE.match(v))),
        )
        # identifier_like: alnum tokens that are NOT plain integers / emails
        maybe(
            C.PATTERN_IDENTIFIER_LIKE,
            _ratio(
                non_empty,
                lambda v: bool(IDENTIFIER_RE.match(v)) and not INT_RE.match(v) and not EMAIL_RE.match(v),
            ),
            threshold=0.95,
        )

    # numeric-range patterns
    if numeric_min is not None and numeric_max is not None:
        if numeric_min >= 0.0 and numeric_max <= 1.0:
            patterns.append(C.PATTERN_RANGE_0_1)
        if numeric_min >= 0.0 and numeric_max <= 4.0:
            patterns.append(C.PATTERN_RANGE_0_4)
        if numeric_min >= 0.0:
            patterns.append(C.PATTERN_POSITIVE_NUMBER)

    if unique_rate >= C.MOSTLY_UNIQUE_THRESHOLD:
        patterns.append(C.PATTERN_MOSTLY_UNIQUE)
    if distinct_count is not None and 0 < distinct_count <= C.ENUM_CARDINALITY_MAX and unique_rate < 0.5:
        patterns.append(C.PATTERN_ENUM_LIKE)
    if null_rate >= C.HIGH_NULL_RATE_THRESHOLD:
        patterns.append(C.PATTERN_HIGH_NULL_RATE)

    # de-dup while preserving order
    seen: set[str] = set()
    ordered: list[str] = []
    for p in patterns:
        if p not in seen:
            seen.add(p)
            ordered.append(p)
    return ordered
