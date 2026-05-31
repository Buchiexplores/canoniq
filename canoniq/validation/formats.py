"""Built-in, local format validators (§9, §14).

Each validator takes a string and returns True/False. Unknown formats are not routed
here; callers fall back to type-only validation.
"""

from __future__ import annotations

import re

from canoniq.core.constants import CURRENCY_CODES

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
_ISO8601_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}([ T]\d{2}:\d{2}(:\d{2})?(\.\d+)?(Z|[+-]\d{2}:?\d{2})?)?$"
)
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_E164_RE = re.compile(r"^\+?[1-9]\d{6,14}$")
_ISO3166_A2_RE = re.compile(r"^[A-Z]{2}$")
_BIC_RE = re.compile(r"^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$")
_POSTAL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9\s\-]{2,9}$")


def is_email(value: str) -> bool:
    return bool(_EMAIL_RE.match(value.strip()))


def is_uuid(value: str) -> bool:
    return bool(_UUID_RE.match(value.strip()))


def is_iso8601(value: str) -> bool:
    return bool(_ISO8601_RE.match(value.strip()))


def is_date(value: str) -> bool:
    return bool(_DATE_RE.match(value.strip()))


def is_e164(value: str) -> bool:
    return bool(_E164_RE.match(value.strip().replace(" ", "").replace("-", "")))


def is_iso3166_alpha2(value: str) -> bool:
    return bool(_ISO3166_A2_RE.match(value.strip().upper()))


def is_iso4217(value: str) -> bool:
    return value.strip().upper() in CURRENCY_CODES


def is_postal_code(value: str) -> bool:
    return bool(_POSTAL_RE.match(value.strip()))


def is_bic(value: str) -> bool:
    return bool(_BIC_RE.match(value.strip().upper()))


def _iban_checksum_ok(value: str) -> bool:
    v = value.strip().replace(" ", "").upper()
    if len(v) < 15 or not v[:2].isalpha() or not v[2:4].isdigit():
        return False
    rearranged = v[4:] + v[:4]
    digits = "".join(str(int(ch, 36)) for ch in rearranged)
    try:
        return int(digits) % 97 == 1
    except ValueError:
        return False


def is_iban(value: str) -> bool:
    return _iban_checksum_ok(value)


def _luhn_ok(digits: str) -> bool:
    total = 0
    reverse = digits[::-1]
    for i, ch in enumerate(reverse):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def is_npi(value: str) -> bool:
    """NPI: 10 digits, Luhn-valid after prefixing 80840 (per CMS spec)."""
    v = value.strip()
    if not (v.isdigit() and len(v) == 10):
        return False
    return _luhn_ok("80840" + v)


def _gtin_checksum_ok(value: str) -> bool:
    v = value.strip()
    if not v.isdigit() or len(v) not in (8, 12, 13, 14):
        return False
    digits = [int(c) for c in v]
    check = digits[-1]
    body = digits[:-1][::-1]
    total = 0
    for i, d in enumerate(body):
        total += d * (3 if i % 2 == 0 else 1)
    calc = (10 - (total % 10)) % 10
    return calc == check


def is_gtin(value: str) -> bool:
    return _gtin_checksum_ok(value)


def is_lei(value: str) -> bool:
    """LEI: 20 chars, ISO 17442; ISO 7064 mod-97-10 checksum."""
    v = value.strip().upper()
    if len(v) != 20 or not v.isalnum():
        return False
    digits = "".join(str(int(ch, 36)) for ch in v)
    try:
        return int(digits) % 97 == 1
    except ValueError:
        return False


# format name → validator
FORMAT_VALIDATORS = {
    "email": is_email,
    "uuid": is_uuid,
    "iso8601": is_iso8601,
    "date": is_date,
    "e164": is_e164,
    "iso3166_alpha2": is_iso3166_alpha2,
    "iso4217": is_iso4217,
    "postal_code": is_postal_code,
    "bic": is_bic,
    "iban": is_iban,
    "npi": is_npi,
    "gtin": is_gtin,
    "lei": is_lei,
}

# formats that carry a checksum (used to pick the `valid_checksum` rule).
CHECKSUM_FORMATS = frozenset({"iban", "gtin", "npi", "lei"})


def validate_format(format_name: str, value: str) -> bool:
    """Validate a value against a named format. Unknown formats pass (degrade gracefully)."""
    validator = FORMAT_VALIDATORS.get(format_name)
    if validator is None:
        return True
    return validator(value)
