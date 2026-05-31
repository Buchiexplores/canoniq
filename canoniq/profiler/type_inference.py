"""Type inference over sampled string values (§11.2).

Rules are ordered; first match wins per value. The column type is the most common
non-unknown per-value verdict, with a small precedence to break ties toward more
specific types.
"""

from __future__ import annotations

import json
import re
from collections import Counter

from canoniq.core.constants import (
    CURRENCY_CODES,
    TYPE_ARRAY,
    TYPE_BOOLEAN,
    TYPE_CURRENCY_CODE,
    TYPE_DATE,
    TYPE_DECIMAL,
    TYPE_EMAIL,
    TYPE_INTEGER,
    TYPE_JSON,
    TYPE_PERCENTAGE,
    TYPE_STRING,
    TYPE_TEXT,
    TYPE_TIMESTAMP,
    TYPE_UNKNOWN,
)

# RFC 5322 subset — good enough for inference, not full validation.
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
INT_RE = re.compile(r"^[+-]?\d+$")
DECIMAL_RE = re.compile(r"^[+-]?(\d+\.\d*|\.\d+|\d+)$")
DATE_RES = (
    re.compile(r"^\d{4}-\d{2}-\d{2}$"),
    re.compile(r"^\d{1,2}/\d{1,2}/\d{4}$"),
    re.compile(r"^\d{1,2}-\d{1,2}-\d{4}$"),
)
DATETIME_RES = (
    re.compile(r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2})?"),
    re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})?$"),
)
PERCENT_RE = re.compile(r"^[+-]?\d+(\.\d+)?\s*%$")

BOOLEAN_TOKENS = {"true", "false", "yes", "no", "y", "n", "t", "f", "0", "1"}
TEXT_AVG_LEN = 60  # avg length above which a string column is considered free text

_PRECEDENCE = {
    TYPE_EMAIL: 9,
    TYPE_CURRENCY_CODE: 8,
    TYPE_BOOLEAN: 7,
    TYPE_INTEGER: 6,
    TYPE_PERCENTAGE: 6,
    TYPE_DECIMAL: 5,
    TYPE_TIMESTAMP: 5,
    TYPE_DATE: 4,
    TYPE_JSON: 4,
    TYPE_ARRAY: 4,
    TYPE_TEXT: 2,
    TYPE_STRING: 1,
    TYPE_UNKNOWN: 0,
}


def infer_value_type(value: str) -> str:
    """Infer the type of a single non-empty string value (first match wins)."""
    v = value.strip()
    if not v:
        return TYPE_UNKNOWN
    if EMAIL_RE.match(v):
        return TYPE_EMAIL
    if len(v) == 3 and v.isalpha() and v.upper() in CURRENCY_CODES:
        return TYPE_CURRENCY_CODE
    if PERCENT_RE.match(v):
        return TYPE_PERCENTAGE
    if INT_RE.match(v):
        return TYPE_INTEGER
    if DECIMAL_RE.match(v) and ("." in v):
        return TYPE_DECIMAL
    if v.lower() in BOOLEAN_TOKENS:
        return TYPE_BOOLEAN
    for rx in DATETIME_RES:
        if rx.match(v):
            return TYPE_TIMESTAMP
    for rx in DATE_RES:
        if rx.match(v):
            return TYPE_DATE
    if v[0] in "[{":
        try:
            parsed = json.loads(v)
            return TYPE_ARRAY if isinstance(parsed, list) else TYPE_JSON
        except (ValueError, TypeError):
            pass
    return TYPE_STRING


def _resolve_boolean(values: list[str]) -> bool:
    """A column is boolean only if its full distinct set is boolean-ish and small."""
    distinct = {v.strip().lower() for v in values if v.strip()}
    return bool(distinct) and distinct.issubset(BOOLEAN_TOKENS) and len(distinct) <= 2


def infer_column_type(values: list[str]) -> str:
    """Infer the dominant type for a column of sampled string values."""
    non_empty = [v for v in values if v is not None and str(v).strip() != ""]
    if not non_empty:
        return TYPE_UNKNOWN

    # 0/1 alone is ambiguous: treat as integer unless the column is clearly boolean.
    verdicts = [infer_value_type(str(v)) for v in non_empty]
    counter = Counter(verdicts)

    # Promote integer→boolean only when the distinct set is a 2-value boolean set
    # made of words (true/false/yes/no), not numeric 0/1.
    word_bools = {"true", "false", "yes", "no", "y", "n", "t", "f"}
    distinct_lower = {str(v).strip().lower() for v in non_empty}
    if distinct_lower and distinct_lower.issubset(word_bools):
        return TYPE_BOOLEAN

    # Numeric column that is entirely integers stays integer; mix of int+decimal → decimal.
    types_present = set(counter)
    if types_present <= {TYPE_INTEGER, TYPE_UNKNOWN} and TYPE_INTEGER in types_present:
        return TYPE_INTEGER
    if types_present <= {TYPE_INTEGER, TYPE_DECIMAL, TYPE_UNKNOWN} and (
        TYPE_DECIMAL in types_present
    ):
        return TYPE_DECIMAL

    # Otherwise pick the most common, breaking ties by precedence.
    best = max(
        counter.items(),
        key=lambda kv: (kv[1], _PRECEDENCE.get(kv[0], 0)),
    )[0]

    # Free-text detection: long strings → text.
    if best == TYPE_STRING:
        avg_len = sum(len(str(v)) for v in non_empty) / len(non_empty)
        if avg_len >= TEXT_AVG_LEN:
            return TYPE_TEXT
    return best
