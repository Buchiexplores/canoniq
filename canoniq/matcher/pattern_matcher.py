"""Pattern signal: overlap between detected patterns and canonical format/semantic_tags (§13)."""

from __future__ import annotations

from canoniq.core import constants as C
from canoniq.core.models import CanonicalField, SourceFieldProfile

# canonical `format` → the source pattern that confirms it.
_FORMAT_TO_PATTERN: dict[str, str] = {
    "email": C.PATTERN_EMAIL,
    "iso8601": C.PATTERN_TIMESTAMP_ISO,
    "date": C.PATTERN_DATE,
    "uuid": C.PATTERN_UUID_LIKE,
    "iso4217": C.PATTERN_CURRENCY_CODE_LIKE,
    "iban": C.PATTERN_IBAN_LIKE,
    "gtin": C.PATTERN_GTIN_LIKE,
    "iso3166_alpha2": C.PATTERN_COUNTRY_CODE_LIKE,
    "postal_code": C.PATTERN_POSTAL_CODE_LIKE,
    "e164": C.PATTERN_PHONE_LIKE,
}

# semantic tag → patterns that support it.
_TAG_TO_PATTERNS: dict[str, set[str]] = {
    "identifier": {C.PATTERN_IDENTIFIER_LIKE, C.PATTERN_UUID_LIKE, C.PATTERN_MOSTLY_UNIQUE},
    "money": {C.PATTERN_DECIMAL, C.PATTERN_CURRENCY_LIKE, C.PATTERN_POSITIVE_NUMBER},
    "timestamp": {C.PATTERN_TIMESTAMP_ISO, C.PATTERN_DATE},
}


def pattern_score(source: SourceFieldProfile, canonical: CanonicalField) -> tuple[float, str | None]:
    patterns = set(source.patterns)
    if not patterns:
        return 0.0, None

    # Strong signal: format confirmed by a matching pattern.
    if canonical.format and canonical.format in _FORMAT_TO_PATTERN:
        wanted = _FORMAT_TO_PATTERN[canonical.format]
        if wanted in patterns:
            return 1.0, f"value pattern '{wanted}' matches format '{canonical.format}'"

    # Semantic-tag overlap.
    best = 0.0
    reason = None
    for tag in canonical.semantic_tags:
        supporting = _TAG_TO_PATTERNS.get(tag, set())
        overlap = supporting & patterns
        if overlap:
            score = min(1.0, 0.6 + 0.2 * len(overlap))
            if score > best:
                best = score
                reason = f"patterns {sorted(overlap)} support semantic tag '{tag}'"

    # enum format alignment.
    if canonical.enum and C.PATTERN_ENUM_LIKE in patterns and best < 0.7:
        best = 0.7
        reason = "low-cardinality values align with canonical enum"

    if best <= 0.0:
        return 0.0, None
    return round(best, 4), reason
