# PATENT REFERENCE — FILING 2026-04-05

This repository, at tag `filing-2026-04-05`, is the observed reference
embodiment for the provisional patent application:

**Title:** System and Method for Detecting, Quantifying, and Classifying
Structural Constraint in Empirical Distributions Using a Ratio-Based
Convergence Framework

**Inventor:** Jair Valley
**Assignee:** Heyer Livin LLC
**Filing Date:** 2026-04-05
**Application Type:** Provisional under 35 U.S.C. § 111(b)

## Files referenced by the filing

| File | Role in claims |
|------|----------------|
| `glyph_constraint.py` | Reference implementation of the claimed method (claims 1–19). Pipeline, partition construction, ratio computation, zone classification, event record generation, schema validation. |
| `event_schema_v1.json` | Stored schema of the machine-readable event record. Schema version `v1`. Convergence band `[0.30, 0.50]`. |

## Locked constants

| Constant | Value |
|----------|-------|
| `LOWER_THRESHOLD` | 0.30 |
| `UPPER_THRESHOLD` | 0.50 |
| `REFERENCE_POINT` | 0.39 |
| `SCHEMA_VERSION` | v1 |
| `RECORD_VERSION` | v1 |
| `THRESHOLD_SET_VERSION` | thresholds_v1_2026-04-05 |

## Reproducibility chain

Every generated event record carries:
- `mapping_rule_version`
- `threshold_set_version`
- `record_version`
- `schema_version`
- `source_id`

A third party in possession of a record and the referenced versions can
replay the computation and verify the result. See `replay_hash()` in
`glyph_constraint.py` (claim 16).

## Post-filing

This repository state is frozen for the filing. Any subsequent changes
to the module will be made on a separate branch and a new schema version
will be cut before any runtime threshold change.
