"""Name signal: fuzzy similarity between normalized names (§13), via RapidFuzz."""

from __future__ import annotations

from rapidfuzz import fuzz

from canoniq.core.models import CanonicalField, SourceFieldProfile
from canoniq.core.util import normalize_name, tokens


def name_score(source: SourceFieldProfile, canonical: CanonicalField) -> tuple[float, str | None]:
    """Return (score, reason). Blends token-set ratio and plain ratio over names+aliases."""
    src = normalize_name(source.name)
    candidates = [normalize_name(canonical.name)] + [normalize_name(a) for a in canonical.aliases]

    best = 0.0
    best_target = canonical.name
    for target in candidates:
        token_ratio = fuzz.token_set_ratio(src, target) / 100.0
        plain_ratio = fuzz.ratio(src, target) / 100.0
        score = max(token_ratio * 0.6 + plain_ratio * 0.4, plain_ratio)
        if score > best:
            best = score
            best_target = target

    # token overlap bonus (shared meaningful tokens)
    shared = tokens(source.name) & tokens(canonical.name)
    if shared and best < 1.0:
        best = min(1.0, best + 0.05 * len(shared))

    if best <= 0.0:
        return 0.0, None
    reason = f"name similarity {best:.2f} ('{source.name}' ~ '{best_target}')"
    return round(best, 4), reason
