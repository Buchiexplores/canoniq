"""Shared constants: canonical types, statuses, patterns, default scoring config."""

from __future__ import annotations

# --- Canonical type system (§11) ---
TYPE_STRING = "string"
TYPE_TEXT = "text"
TYPE_INTEGER = "integer"
TYPE_DECIMAL = "decimal"
TYPE_BOOLEAN = "boolean"
TYPE_DATE = "date"
TYPE_TIMESTAMP = "timestamp"
TYPE_EMAIL = "email"
TYPE_CURRENCY_CODE = "currency_code"
TYPE_PERCENTAGE = "percentage"
TYPE_JSON = "json"
TYPE_ARRAY = "array"
TYPE_UNKNOWN = "unknown"

CANONICAL_TYPES: tuple[str, ...] = (
    TYPE_STRING, TYPE_TEXT, TYPE_INTEGER, TYPE_DECIMAL, TYPE_BOOLEAN,
    TYPE_DATE, TYPE_TIMESTAMP, TYPE_EMAIL, TYPE_CURRENCY_CODE,
    TYPE_PERCENTAGE, TYPE_JSON, TYPE_ARRAY, TYPE_UNKNOWN,
)

# --- Mapping statuses (§13.2) ---
STATUS_AUTO_APPROVED = "auto_approved"
STATUS_REQUIRES_REVIEW = "requires_review"
STATUS_LOW_CONFIDENCE = "low_confidence"
STATUS_UNMAPPED = "unmapped"
STATUS_APPROVED = "approved"  # human-promoted

# --- Default confidence thresholds (§13.2, configurable) ---
DEFAULT_AUTO_APPROVE_THRESHOLD = 0.90
DEFAULT_REVIEW_THRESHOLD = 0.70
# Minimum confidence floor below which a candidate is treated as no-candidate.
DEFAULT_MAPPING_FLOOR = 0.30

# --- Default scoring weights (§13.1). Must sum to 1.0 when semantic disabled. ---
DEFAULT_WEIGHTS: dict[str, float] = {
    "alias": 0.40,
    "name": 0.20,
    "type": 0.15,
    "pattern": 0.15,
    "range": 0.10,
    "semantic": 0.0,
}

# --- Sampling defaults (§17.3) ---
DEFAULT_SAMPLE_LIMIT = 1000
DEFAULT_MAX_FILES = 5
DEFAULT_ROWS_PER_FILE = 1000

# --- Profiling defaults ---
DEFAULT_SAMPLE_VALUES = 5
ENUM_CARDINALITY_MAX = 20  # distinct count at/below which a field is an enum candidate

# --- Detected patterns (§12.1) ---
PATTERN_EMAIL = "email"
PATTERN_IDENTIFIER_LIKE = "identifier_like"
PATTERN_UUID_LIKE = "uuid_like"
PATTERN_DECIMAL = "decimal"
PATTERN_INTEGER = "integer"
PATTERN_RANGE_0_1 = "range_0_to_1"
PATTERN_RANGE_0_4 = "range_0_to_4"
PATTERN_POSITIVE_NUMBER = "positive_number"
PATTERN_TIMESTAMP_ISO = "timestamp_iso"
PATTERN_DATE = "date"
PATTERN_MOSTLY_UNIQUE = "mostly_unique"
PATTERN_ENUM_LIKE = "enum_like"
PATTERN_HIGH_NULL_RATE = "high_null_rate"
PATTERN_CURRENCY_LIKE = "currency_like"
PATTERN_CURRENCY_CODE_LIKE = "currency_code_like"
PATTERN_POSTAL_CODE_LIKE = "postal_code_like"
PATTERN_PHONE_LIKE = "phone_like"
PATTERN_IBAN_LIKE = "iban_like"
PATTERN_GTIN_LIKE = "gtin_like"
PATTERN_COUNTRY_CODE_LIKE = "country_code_like"

# --- PII / PHI flags (§12.2) ---
PII_FLAGS: tuple[str, ...] = (
    "email", "phone", "name", "national_id", "dob",
    "address", "mrn", "account_number", "ip_address",
)
HIGH_PII_FLAGS: tuple[str, ...] = ("national_id", "mrn", "account_number")

# --- PII sensitivity levels on canonical fields ---
PII_LEVELS: tuple[str, ...] = ("none", "low", "moderate", "high", "phi")

# --- ISO 4217 currency codes (common subset; format validator covers full set) ---
CURRENCY_CODES: frozenset[str] = frozenset({
    "USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY", "HKD", "NZD",
    "SEK", "KRW", "SGD", "NOK", "MXN", "INR", "RUB", "ZAR", "TRY", "BRL",
    "DKK", "PLN", "THB", "IDR", "HUF", "CZK", "ILS", "CLP", "PHP", "AED",
    "SAR", "MYR", "RON", "NGN", "KES", "GHS",
})

HIGH_NULL_RATE_THRESHOLD = 0.50
MOSTLY_UNIQUE_THRESHOLD = 0.90

PROFILER_VERSION = "0.1.0"
