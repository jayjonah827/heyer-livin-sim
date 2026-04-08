from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


class CulturalLevel(Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    TERTIARY = "tertiary"


class ResponseType(Enum):
    SPEC = "spec"
    DEFINITION = "definition"
    ARTIFACT = "artifact"
    CODE = "code"


class AuditAction(Enum):
    EVENT_ADDED = "event_added"
    CONTEXT_ADDED = "context_added"
    RESPONSE_GENERATED = "response_generated"
    BAND_EVALUATED = "band_evaluated"
    REPORT_CREATED = "report_created"


@dataclass
class ContextReference:
    ref_id: str
    title: str
    text: str
    tags: List[str] = field(default_factory=list)
    source: str = ""


@dataclass
class AuditEntry:
    timestamp: str
    action: AuditAction
    message: str
    metadata: Dict[str, object] = field(default_factory=dict)


@dataclass
class GlyphEvent:
    event_id: str
    source: str
    timestamp: str
    user_probability: float
    category: str
    description: str
    data: Dict[str, object] = field(default_factory=dict)
    level: CulturalLevel = CulturalLevel.SECONDARY
    band: str = "gamma"
    vector: Dict[str, float] = field(default_factory=dict)


@dataclass
class EventResponse:
    response_type: ResponseType
    title: str
    body: str
    confidence: float
    metadata: Dict[str, object] = field(default_factory=dict)


class BehaviorAnalytics:
    def __init__(self) -> None:
        self.events: List[GlyphEvent] = []
        self.counts: Dict[str, int] = {}
        self.probability_index: Dict[str, float] = {}
        self.context_references: List[ContextReference] = []
        self.audit_trail: List[AuditEntry] = []

    def add_audit(self, action: AuditAction, message: str, metadata: Optional[Dict[str, object]] = None) -> None:
        self.audit_trail.append(
            AuditEntry(
                timestamp=datetime.utcnow().isoformat() + 'Z',
                action=action,
                message=message,
                metadata=metadata or {},
            )
        )

    def add_event(self, event: GlyphEvent) -> None:
        self.events.append(event)
        self.counts[event.category] = self.counts.get(event.category, 0) + 1
        self.probability_index[event.event_id] = event.user_probability
        self.add_audit(AuditAction.EVENT_ADDED, f"Added event {event.event_id}", {
            "category": event.category,
            "level": event.level.value,
            "band": event.band,
        })

    def add_context_reference(self, reference: ContextReference) -> None:
        self.context_references.append(reference)
        self.add_audit(AuditAction.CONTEXT_ADDED, f"Added context reference {reference.ref_id}", {
            "tags": reference.tags,
            "source": reference.source,
        })

    def most_cultural_levels(self) -> Sequence[Tuple[CulturalLevel, int]]:
        level_counts: Dict[CulturalLevel, int] = {
            CulturalLevel.PRIMARY: 0,
            CulturalLevel.SECONDARY: 0,
            CulturalLevel.TERTIARY: 0,
        }
        for event in self.events:
            level_counts[event.level] += 1
        return sorted(level_counts.items(), key=lambda kv: kv[1], reverse=True)

    def category_probability(self, category: str) -> float:
        total = len(self.events)
        if total == 0:
            return 0.0
        return self.counts.get(category, 0) / total

    def update_probability(self, event_id: str, adjustment: float) -> None:
        if event_id in self.probability_index:
            self.probability_index[event_id] = max(0.0, min(1.0, self.probability_index[event_id] + adjustment))

    def vectorize_event(self, event: GlyphEvent) -> Dict[str, float]:
        length_weight = min(1.0, len(event.description) / 300)
        category_weight = 0.8 if event.category == 'knowledge' else 0.6
        level_weight = {
            CulturalLevel.PRIMARY: 1.0,
            CulturalLevel.SECONDARY: 0.75,
            CulturalLevel.TERTIARY: 0.5,
        }[event.level]
        vector = {
            'probability': event.user_probability,
            'length': length_weight,
            'category': category_weight,
            'level': level_weight,
        }
        event.vector = vector
        return vector

    def evaluate_band(self, event: GlyphEvent) -> str:
        vector = self.vectorize_event(event)
        score = (vector['probability'] + vector['length'] + vector['category'] + vector['level']) / 4.0
        if score >= 0.78:
            band = 'alpha'
        elif score >= 0.55:
            band = 'beta'
        else:
            band = 'gamma'
        event.band = band
        self.add_audit(AuditAction.BAND_EVALUATED, f"Evaluated band {band} for event {event.event_id}", {
            'score': score,
            'vector': vector,
        })
        return band

    def overall_band_score(self) -> float:
        if not self.events:
            return 0.0
        return sum(event.user_probability for event in self.events) / len(self.events)

    def get_context_for_reasoning(self, tags: Sequence[str]) -> List[ContextReference]:
        matched = [ref for ref in self.context_references if any(tag in ref.tags for tag in tags)]
        return matched[:5]

    def evaluate_entry(self, entry: str) -> Dict[str, object]:
        matches = sum(1 for event in self.events if event.description in entry or event.category in entry)
        score = matches / max(1, len(self.events))
        self.add_audit(AuditAction.RESPONSE_GENERATED, "Evaluated entry against prior data", {
            'entry_sample': entry[:120],
            'match_score': score,
            'events': len(self.events),
        })
        return {
            "match_score": score,
            "events": len(self.events),
            "most_likely_category": max(self.counts, key=self.counts.get) if self.counts else None,
        }

    def build_organizational_report(self) -> str:
        band_score = self.overall_band_score()
        report = [
            'Glyph organizational report',
            f'Total events: {len(self.events)}',
            f'Overall band probability mean: {band_score:.3f}',
            f'Most cultural levels: {self.most_cultural_levels()}',
            f'Context references: {len(self.context_references)}',
        ]
        self.add_audit(AuditAction.REPORT_CREATED, 'Created organizational report', {
            'total_events': len(self.events),
            'band_score': band_score,
        })
        return '\n'.join(report)


class ProbabilityEngine:
    def __init__(self, analytics: BehaviorAnalytics) -> None:
        self.analytics = analytics

    def event_probability(self, category: str, base_rate: float = 0.5) -> float:
        category_prob = self.analytics.category_probability(category)
        vector_mean = self.analytics.overall_band_score()
        return min(1.0, max(0.0, (base_rate + category_prob + vector_mean) / 3.0))

    def choose_next_question(self, categories: Sequence[str]) -> Optional[str]:
        if not categories:
            return None
        ranked = sorted(categories, key=lambda c: self.analytics.category_probability(c), reverse=True)
        return ranked[0]

    def arcade_probability(self, choice_weight: float, current_bias: float) -> float:
        result = (choice_weight * 0.7) + (current_bias * 0.3)
        return min(1.0, max(0.0, result))

    def simplified_decision_band(self, entry: str, count: int = 3) -> List[str]:
        analysis_value = len(entry.split()) / max(1, len(self.analytics.events))
        choices = ['alpha', 'beta', 'gamma']
        ranked = sorted(choices, key=lambda band: abs(0.5 - analysis_value - (0.1 * choices.index(band))))
        return ranked[:count]


class GlyphArtifactBuilder:
    def __init__(self, analytics: BehaviorAnalytics) -> None:
        self.analytics = analytics

    def paleographic_font_spec(self, source: str, math_style: str) -> str:
        return (
            f"Font system from source={source}, math_style={math_style}, "
            f"derived_from_events={len(self.analytics.events)}"
        )

    def glyph_for_designer(self, designer_name: str, theme: str) -> str:
        return (
            f"Glyph package for {designer_name}, theme={theme}, "
            f"priority={self.analytics.most_cultural_levels()[0][0].value if self.analytics.events else 'unknown'}"
        )


class GlyphEngine:
    def __init__(self) -> None:
        self.analytics = BehaviorAnalytics()
        self.probability = ProbabilityEngine(self.analytics)
        self.builder = GlyphArtifactBuilder(self.analytics)

    def add_context_reference(self, reference: ContextReference) -> None:
        self.analytics.add_context_reference(reference)

    def add_event(self, event: GlyphEvent) -> None:
        event.level = self.categorize_event(event)
        self.analytics.evaluate_band(event)
        self.analytics.add_event(event)

    def categorize_event(self, event: GlyphEvent) -> CulturalLevel:
        if event.user_probability >= 0.8:
            return CulturalLevel.PRIMARY
        if event.user_probability >= 0.4:
            return CulturalLevel.SECONDARY
        return CulturalLevel.TERTIARY

    def reference_for_reasoning(self, tags: Sequence[str]) -> List[ContextReference]:
        return self.analytics.get_context_for_reasoning(tags)

    def process_event(self, event: GlyphEvent, scope_terms: Sequence[str] = ()) -> EventResponse:
        if scope_terms and not self.strict_scope_check(event.description, scope_terms):
            return EventResponse(
                response_type=ResponseType.DEFINITION,
                title="Out of scope",
                body="The event description does not contain scope-aligned terms, so the response remains focused on core math and structure.",
                confidence=0.0,
                metadata={"reason": "scope mismatch"},
            )

        self.add_event(event)
        evaluation = self.analytics.evaluate_entry(event.description)
        simplified_band = self.probability.simplified_decision_band(event.description)
        response_type = ResponseType.SPEC if event.level == CulturalLevel.PRIMARY else ResponseType.DEFINITION
        return EventResponse(
            response_type=response_type,
            title=f"Response for {event.event_id}",
            body=(
                f"Processed event in category={event.category}, band={event.band}, level={event.level.value}. "
                f"Match score={evaluation['match_score']:.2f}. "
                f"Decision band candidates={simplified_band}."
            ),
            confidence=self.probability.event_probability(event.category, event.user_probability),
            metadata={
                "evaluation": evaluation,
                "simplified_band": simplified_band,
                "band_mean": self.analytics.overall_band_score(),
            },
        )

    def generate_candidates(self, entry: str, count: int = 3) -> List[EventResponse]:
        candidates: List[EventResponse] = []
        base_confidence = self.analytics.evaluate_entry(entry)["match_score"]
        band_candidates = self.probability.simplified_decision_band(entry, count)
        for idx, response_type in enumerate(ResponseType):
            candidates.append(
                EventResponse(
                    response_type=response_type,
                    title=f"Candidate {idx + 1}: {response_type.value}",
                    body=(
                        f"Generated {response_type.value} for entry: {entry[:80]}. "
                        f"Decision band={band_candidates[idx] if idx < len(band_candidates) else 'gamma'}."
                    ),
                    confidence=min(1.0, base_confidence + 0.1 * idx),
                )
            )
            if len(candidates) >= count:
                break
        return candidates

    def build_glyph_artifact(self, source: str, math_style: str, designer_name: str, theme: str) -> str:
        return self.builder.glyph_for_designer(designer_name, theme)

    def build_structural_spec(self, event: GlyphEvent) -> str:
        return self.builder.build_architectural_spec(event)

    def strict_scope_check(self, question: str, scope_terms: Sequence[str]) -> bool:
        return any(term in question.lower() for term in scope_terms)

    def event_based_response(self, event: GlyphEvent, scope_terms: Sequence[str]) -> EventResponse:
        return self.process_event(event, scope_terms=scope_terms)

    def organizational_report(self) -> str:
        return self.analytics.build_organizational_report()


def default_event_engine() -> GlyphEngine:
    return GlyphEngine()
