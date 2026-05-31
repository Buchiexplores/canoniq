"""Mapping engine: combine signals into scored, gated, explained suggestions (§13).

Deterministic given the same inputs + config. Enforces the assignment constraint
that each canonical field is claimed by at most one source field.
"""

from __future__ import annotations

from dataclasses import dataclass

from canoniq.ai.base import BaseAIMatcher
from canoniq.config import CanonIQConfig
from canoniq.core.constants import STATUS_UNMAPPED
from canoniq.core.models import (
    CanonicalEntity,
    CanonicalField,
    MappingResult,
    MappingSuggestion,
    SourceFieldProfile,
    SourceProfile,
)
from canoniq.core.util import now_iso
from canoniq.matcher.alias_matcher import alias_score
from canoniq.matcher.name_matcher import name_score
from canoniq.matcher.pattern_matcher import pattern_score
from canoniq.matcher.range_matcher import range_score
from canoniq.matcher.type_matcher import type_score
from canoniq.scoring.confidence import combine_confidence, status_for_confidence


@dataclass
class _Candidate:
    source_field: str
    canonical_field: str
    confidence: float
    status: str
    reasons: list[str]
    signals: dict
    alias_hit: bool
    name_sig: float


class MappingEngine:
    def __init__(self, config: CanonIQConfig | None = None, ai_matcher: BaseAIMatcher | None = None):
        self.config = config or CanonIQConfig()
        self.ai_matcher = ai_matcher

    def _score_pair(
        self, source: SourceFieldProfile, canonical: CanonicalField
    ) -> _Candidate:
        a_score, a_reason = alias_score(source, canonical)
        n_score, n_reason = name_score(source, canonical)
        t_score, t_reason = type_score(source, canonical)
        p_score, p_reason = pattern_score(source, canonical)
        r_score, r_reason = range_score(source, canonical)

        signals = {
            "alias": a_score,
            "name": n_score,
            "type": t_score,
            "pattern": p_score,
            "range": r_score,
        }
        if self.ai_matcher is not None and self.config.weights.get("semantic", 0.0) > 0.0:
            signals["semantic"] = self.ai_matcher.semantic_score(source, canonical)

        confidence = combine_confidence(signals, self.config.weights)
        status = status_for_confidence(
            confidence,
            auto_threshold=self.config.auto_approve_threshold,
            review_threshold=self.config.review_threshold,
        )
        reasons = [r for r in (a_reason, n_reason, t_reason, p_reason, r_reason) if r]
        return _Candidate(
            source_field=source.name,
            canonical_field=canonical.name,
            confidence=confidence,
            status=status,
            reasons=reasons,
            signals=signals,
            alias_hit=a_score >= 1.0,
            name_sig=n_score,
        )

    def suggest(self, profile: SourceProfile, schema: CanonicalEntity) -> MappingResult:
        floor = self.config.mapping_floor

        # Score every (source, canonical) pair above the floor.
        per_source: dict[str, list[_Candidate]] = {}
        for src in profile.fields:
            cands: list[_Candidate] = []
            for canonical in schema.fields.values():
                cand = self._score_pair(src, canonical)
                if cand.confidence >= floor:
                    cands.append(cand)
            cands.sort(
                key=lambda c: (c.confidence, c.alias_hit, c.name_sig, -_pos(profile, c.source_field)),
                reverse=True,
            )
            per_source[src.name] = cands

        # Greedy assignment: a canonical field is claimed by at most one source.
        # Order sources by their best candidate confidence (desc), deterministic.
        claimed: set[str] = set()
        suggestions: list[MappingSuggestion] = []

        ordered_sources = sorted(
            profile.fields,
            key=lambda f: (
                -(per_source[f.name][0].confidence if per_source[f.name] else 0.0),
                f.position if f.position is not None else 0,
                f.name,
            ),
        )

        decided: dict[str, MappingSuggestion] = {}
        for src in ordered_sources:
            chosen: MappingSuggestion | None = None
            for cand in per_source[src.name]:
                if cand.canonical_field in claimed:
                    continue
                claimed.add(cand.canonical_field)
                chosen = MappingSuggestion(
                    source_field=cand.source_field,
                    canonical_field=cand.canonical_field,
                    confidence=cand.confidence,
                    status=cand.status,
                    reasons=cand.reasons,
                    signals=cand.signals,
                )
                break
            if chosen is None:
                chosen = MappingSuggestion(
                    source_field=src.name,
                    canonical_field=None,
                    confidence=0.0,
                    status=STATUS_UNMAPPED,
                    reasons=["no canonical candidate above the mapping floor"],
                    signals={},
                )
            decided[src.name] = chosen

        # Emit in original source column order for stable, readable output.
        # Record each source field's inferred type in signals so drift detection can
        # compare types across ingestions without re-profiling the old data.
        for src in profile.fields:
            suggestion = decided[src.name]
            enriched = dict(suggestion.signals)
            enriched["_inferred_type"] = src.inferred_type
            suggestions.append(suggestion.model_copy(update={"signals": enriched}))

        return MappingResult(
            canonical={"domain": schema.domain, "entity": schema.entity, "version": schema.version},
            mappings=suggestions,
            canoniq_version=profile.canoniq_version,
            created_at=now_iso(),
        )


def _pos(profile: SourceProfile, name: str) -> int:
    f = profile.field(name)
    return f.position if f and f.position is not None else 0
