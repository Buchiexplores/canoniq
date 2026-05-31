"""Local heuristic PII/PHI detection and value masking (§12.2).

Detection uses both the field name and sampled values. High-PII fields have their
sample values masked before they ever leave the profiler.
"""

from __future__ import annotations

import re

from canoniq.core.constants import HIGH_PII_FLAGS
from canoniq.core.util import normalize_name
from canoniq.profiler.type_inference import EMAIL_RE

# Field-name keyword → PII flag.
_NAME_SIGNALS: dict[str, tuple[str, ...]] = {
    "email": ("email", "e_mail"),
    "phone": ("phone", "mobile", "cell", "telephone", "fax"),
    "name": ("first_name", "last_name", "given_name", "family_name", "full_name",
             "surname", "fname", "lname"),
    "national_id": ("ssn", "social_security", "national_id", "nino", "tax_id", "passport"),
    "dob": ("dob", "birth_date", "birthdate", "date_of_birth"),
    "address": ("address", "street", "addr", "postal", "zip", "zipcode"),
    "mrn": ("mrn", "medical_record", "patient_mrn"),
    "account_number": ("account_number", "acct_num", "iban", "account_no", "card_number"),
    "ip_address": ("ip_address", "ip_addr", "client_ip"),
}

_SSN_RE = re.compile(r"^\d{3}-\d{2}-\d{4}$")
_IP_RE = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$")


def detect_pii_flags(field_name: str, sample_values: list[str]) -> list[str]:
    """Return PII/PHI flags for a field based on its name and values."""
    norm = normalize_name(field_name)
    flags: list[str] = []

    for flag, keywords in _NAME_SIGNALS.items():
        if any(kw in norm for kw in keywords):
            flags.append(flag)

    non_empty = [str(v).strip() for v in sample_values if v is not None and str(v).strip()]
    if non_empty:
        if "email" not in flags and all(EMAIL_RE.match(v) for v in non_empty):
            flags.append("email")
        if "national_id" not in flags and any(_SSN_RE.match(v) for v in non_empty):
            flags.append("national_id")
        if "ip_address" not in flags and all(_IP_RE.match(v) for v in non_empty):
            flags.append("ip_address")

    # de-dup, stable order
    seen: set[str] = set()
    out: list[str] = []
    for f in flags:
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out


def _mask_email(value: str) -> str:
    try:
        local, domain = value.split("@", 1)
    except ValueError:
        return "***"
    head = local[0] if local else ""
    return f"{head}***@***"


def mask_value(value: str, flags: list[str]) -> str:
    """Mask a single sample value according to its PII flags."""
    v = str(value)
    if not v:
        return v
    if "email" in flags:
        return _mask_email(v)
    # generic high-PII masking: keep first char, redact the rest
    if v.isdigit() and len(v) > 2:
        return v[0] + "*" * (len(v) - 1)
    if len(v) <= 2:
        return "*" * len(v)
    return v[0] + "*" * (len(v) - 1)


def should_mask(flags: list[str]) -> bool:
    """High-sensitivity flags trigger masking of sample values."""
    if not flags:
        return False
    if any(f in HIGH_PII_FLAGS for f in flags):
        return True
    # email/name/dob/address/phone are masked too (moderate+), to be privacy-safe by default
    return any(f in {"email", "name", "dob", "address", "phone", "ip_address"} for f in flags)
