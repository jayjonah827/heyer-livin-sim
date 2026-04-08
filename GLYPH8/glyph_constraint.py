"""
glyph_constraint.py

Reference implementation of the method and system claimed in the
Provisional Patent Application filed 2026-04-05 by Jair Valley
(Heyer Livin LLC):

    "System and Method for Detecting, Quantifying, and Classifying
     Structural Constraint in Empirical Distributions Using a
     Ratio-Based Convergence Framework"

This module is the observed embodiment referenced by the filing. The
threshold values, field names, and pipeline ordering are locked to the
filing packet (FINAL_PATENT_PACKET_2026-04-05.docx) and the stored
schema (event_schema_v1.json, schema version v1).

Pipeline:
    1. receive empirical distribution input data
    2. apply declared domain-mapping rules
    3. construct first and second complementary partitions (MECE)
    4. compute structural-constraint ratio R = x / (x + y**2)
    5. compare ratio to stored thresholds (0.30, 0.50)
    6. assign classification zone (SUBORDINATED / STRUCTURAL / DOMINANT)
    7. optionally validate against reference models
    8. generate structured machine-readable event record
    9. validate schema and version compatibility
   10. store / output validated event record

Reproducibility is preserved through mapping-rule versioning,
threshold-set versioning, source identifiers, and record versions.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple


# --------------------------------------------------------------------------
# Versioning constants (locked for filing 2026-04-05)
# --------------------------------------------------------------------------

SCHEMA_VERSION = "v1"
RECORD_VERSION = "v1"
THRESHOLD_SET_VERSION = "thresholds_v1_2026-04-05"

LOWER_THRESHOLD = 0.30
UPPER_THRESHOLD = 0.50
REFERENCE_POINT = 0.39


# --------------------------------------------------------------------------
# Declared domain-mapping rules (step 2 of the claimed method)
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class MappingRule:
    """
    A declared domain-mapping rule. Identified by version. Declared PRIOR
    to computation (the method halts if no rule is supplied).
    """
    mapping_rule_version: str
    domain: str
    a_field: str          # structural parameter a
    b_field: str          # structural parameter b
    c_field: str          # structural parameter c
    x_selector: Callable[[Dict[str, Any]], float]  # first partition
    y_selector: Callable[[Dict[str, Any]], float]  # second partition
    defined_scope: str    # MECE scope description


# --------------------------------------------------------------------------
# Partition construction (step 3) with MECE verification
# --------------------------------------------------------------------------

@dataclass
class Partitions:
    x: float
    y: float

    def verify_mece(self, total: Optional[float] = None, tol: float = 1e-9) -> bool:
        """
        Mutually exclusive and collectively exhaustive check within scope.
        x and y must be non-negative, not both zero, and (if a total is
        supplied) must sum to the total within tolerance.
        """
        if self.x < 0 or self.y < 0:
            return False
        if self.x == 0 and self.y == 0:
            return False
        if total is not None and abs((self.x + self.y) - total) > tol:
            return False
        return True


def construct_partitions(
    input_data: Dict[str, Any],
    rule: MappingRule,
    total: Optional[float] = None,
) -> Partitions:
    """Step 3: construct first and second partitions from observable source fields."""
    x = float(rule.x_selector(input_data))
    y = float(rule.y_selector(input_data))
    parts = Partitions(x=x, y=y)
    if not parts.verify_mece(total=total):
        raise ValueError(
            "MECE verification failed; partitions are not mutually exclusive "
            "and collectively exhaustive within the defined scope."
        )
    return parts


# --------------------------------------------------------------------------
# Ratio computation (step 4)
# --------------------------------------------------------------------------

def compute_structural_constraint_ratio(parts: Partitions) -> float:
    """
    R = x / (x + y**2)

    Returns a dimensionless ratio in [0, 1]. The squaring of the second
    partition produces the asymmetric denominator that amplifies deviation
    from equipartition under structural constraint.
    """
    denom = parts.x + (parts.y ** 2)
    if denom == 0:
        raise ZeroDivisionError("Ratio denominator is zero; partitions are degenerate.")
    r = parts.x / denom
    if r < 0.0 or r > 1.0:
        raise ValueError(f"Ratio {r} outside [0, 1]; inputs are out of bounds.")
    return r


# --------------------------------------------------------------------------
# Threshold comparison and zone classification (steps 5 and 6)
# --------------------------------------------------------------------------

SUBORDINATED = "SUBORDINATED"
STRUCTURAL = "STRUCTURAL"
DOMINANT = "DOMINANT"


def classify_zone(
    ratio: float,
    lower: float = LOWER_THRESHOLD,
    upper: float = UPPER_THRESHOLD,
) -> str:
    if ratio < lower:
        return SUBORDINATED
    if ratio < upper:
        return STRUCTURAL
    return DOMINANT


# --------------------------------------------------------------------------
# Optional reference-model validation (step 7)
# --------------------------------------------------------------------------

@dataclass
class ReferenceModel:
    name: str
    expected_ratio: float
    tolerance: float


def validate_against_reference(
    ratio: float,
    reference: ReferenceModel,
) -> Dict[str, Any]:
    delta = abs(ratio - reference.expected_ratio)
    return {
        "reference_name": reference.name,
        "expected_ratio": reference.expected_ratio,
        "tolerance": reference.tolerance,
        "delta": delta,
        "consistent": delta <= reference.tolerance,
    }


# --------------------------------------------------------------------------
# Event record generation (step 8) and schema validation (step 9)
# --------------------------------------------------------------------------

def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def generate_event_record(
    *,
    source_id: str,
    domain: str,
    source_type: str,
    title: str,
    cycle_definition: Dict[str, Any],
    irreversible_event: Dict[str, Any],
    ratio: float,
    zone: str,
    mapping_rule_version: str,
    threshold_set_version: str = THRESHOLD_SET_VERSION,
    reference_validation: Optional[Dict[str, Any]] = None,
    run_id: Optional[str] = None,
    tick_id: Optional[str] = None,
    parent_record_id: Optional[str] = None,
    linked_records: Optional[List[str]] = None,
    linked_files: Optional[List[str]] = None,
    notes: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Step 8: build the structured machine-readable event record."""
    record_id = "gev_" + uuid.uuid4().hex[:12]
    inside_band = (LOWER_THRESHOLD <= ratio <= UPPER_THRESHOLD)
    distance = abs(ratio - REFERENCE_POINT)

    record: Dict[str, Any] = {
        "record_id": record_id,
        "source_id": source_id,
        "domain": domain,
        "source_type": source_type,
        "title": title,
        "cycle_definition": cycle_definition,
        "irreversible_event": irreversible_event,
        "metrics": {
            "clustering_ratio": ratio,
            "reference_point": REFERENCE_POINT,
            "convergence_band_min": LOWER_THRESHOLD,
            "convergence_band_max": UPPER_THRESHOLD,
            "inside_band": inside_band,
            "distance_from_reference": distance,
        },
        "routing": {
            "route": "research",
            "status": "live",
        },
        "snapshot": {
            "snapshot_time": _utc_now_iso(),
            "run_id": run_id or uuid.uuid4().hex[:12],
            "tick_id": tick_id or "tick_0001",
            "version": SCHEMA_VERSION,
        },
        "relations": {
            "parent_record_id": parent_record_id,
            "linked_records": linked_records or [],
            "linked_files": linked_files or [],
        },
        "notes": notes or {
            "method_note": f"Zone={zone}; mapping_rule_version={mapping_rule_version}",
            "confidence_note": "Computed per filing 2026-04-05 reference embodiment.",
            "review_note": "",
        },
        # Reproducibility chain (step 12)
        "reproducibility": {
            "mapping_rule_version": mapping_rule_version,
            "threshold_set_version": threshold_set_version,
            "record_version": RECORD_VERSION,
            "schema_version": SCHEMA_VERSION,
            "reference_validation": reference_validation,
        },
    }

    _validate_schema(record)
    return record


REQUIRED_TOP_LEVEL = [
    "record_id", "source_id", "domain", "source_type", "title",
    "cycle_definition", "irreversible_event", "metrics", "routing",
    "snapshot", "relations", "notes",
]

REQUIRED_METRICS = [
    "clustering_ratio", "reference_point", "convergence_band_min",
    "convergence_band_max", "inside_band", "distance_from_reference",
]


def _validate_schema(record: Dict[str, Any]) -> None:
    """Step 9: schema and version compatibility check."""
    for f in REQUIRED_TOP_LEVEL:
        if f not in record:
            raise ValueError(f"Schema validation failed: missing field {f!r}")
    for f in REQUIRED_METRICS:
        if f not in record["metrics"]:
            raise ValueError(f"Schema validation failed: missing metrics field {f!r}")
    if record["snapshot"]["version"] != SCHEMA_VERSION:
        raise ValueError(
            f"Schema version mismatch: got {record['snapshot']['version']}, "
            f"expected {SCHEMA_VERSION}"
        )
    if record["metrics"]["convergence_band_min"] != LOWER_THRESHOLD:
        raise ValueError("convergence_band_min does not match threshold set.")
    if record["metrics"]["convergence_band_max"] != UPPER_THRESHOLD:
        raise ValueError("convergence_band_max does not match threshold set.")


# --------------------------------------------------------------------------
# End-to-end pipeline (claims 1 and 11)
# --------------------------------------------------------------------------

def run_pipeline(
    *,
    input_data: Dict[str, Any],
    rule: MappingRule,
    source_id: str,
    title: str,
    source_type: str,
    cycle_definition: Dict[str, Any],
    irreversible_event: Dict[str, Any],
    total: Optional[float] = None,
    reference: Optional[ReferenceModel] = None,
) -> Dict[str, Any]:
    """
    Execute the claimed method end-to-end. Returns a validated event
    record ready to be stored or output.
    """
    # Step 2: mapping rule already declared (rule argument)
    if rule is None or not rule.mapping_rule_version:
        raise ValueError("Declared domain-mapping rule required before computation.")

    # Step 3
    parts = construct_partitions(input_data, rule, total=total)

    # Step 4
    ratio = compute_structural_constraint_ratio(parts)

    # Step 5 and 6
    zone = classify_zone(ratio)

    # Step 7 (optional)
    reference_validation = None
    if reference is not None:
        reference_validation = validate_against_reference(ratio, reference)

    # Steps 8 and 9
    record = generate_event_record(
        source_id=source_id,
        domain=rule.domain,
        source_type=source_type,
        title=title,
        cycle_definition=cycle_definition,
        irreversible_event=irreversible_event,
        ratio=ratio,
        zone=zone,
        mapping_rule_version=rule.mapping_rule_version,
        reference_validation=reference_validation,
    )

    return record


# --------------------------------------------------------------------------
# Deterministic replay hash (claim 16)
# --------------------------------------------------------------------------

def replay_hash(record: Dict[str, Any]) -> str:
    """
    Hash the metrics and reproducibility fields of a record. Two executions
    on identical input with identical mapping-rule version and threshold-set
    version produce identical hashes.
    """
    payload = {
        "metrics": record["metrics"],
        "reproducibility": record["reproducibility"],
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


# --------------------------------------------------------------------------
# Minimal smoke test
# --------------------------------------------------------------------------

if __name__ == "__main__":
    demo_rule = MappingRule(
        mapping_rule_version="mapping_v1_demo_2026-04-05",
        domain="research",
        a_field="category",
        b_field="segment",
        c_field="period",
        x_selector=lambda d: d["x"],
        y_selector=lambda d: d["y"],
        defined_scope="demo_partition_scope",
    )
    demo_input = {"x": 0.39, "y": 0.61, "category": "demo", "segment": "a", "period": "2026"}
    demo_record = run_pipeline(
        input_data=demo_input,
        rule=demo_rule,
        source_id="source_demo_001",
        title="Demo constraint measurement",
        source_type="dataset",
        cycle_definition={
            "cycle_start": "2026-04-05T00:00:00Z",
            "cycle_end": "2026-04-05T23:59:59Z",
            "cycle_length": 1,
            "cycle_unit": "day",
        },
        irreversible_event={
            "event_name": "demo_event",
            "event_definition": "demo reference event for smoke test",
            "event_position": 0.39,
            "event_unit": "ratio",
        },
        reference=ReferenceModel(name="attractor_0.39", expected_ratio=0.39, tolerance=0.05),
    )
    print(json.dumps(demo_record, indent=2))
    print("replay_hash:", replay_hash(demo_record))
