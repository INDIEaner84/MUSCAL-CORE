# Drift Detector Specification

**Version:** 1.0
**Status:** Specification

---

## 1. Purpose

Detect semantic drift between architecture decisions (ADRs, RFCs) and their
implementation in code, documentation, and tests.

---

## 2. Scan Scope

- `spec/ADR-*.md`, `archive/history/adrs/*` (decisions)
- `runtime/kernel/*`, `features/*` (implementation)
- `docs/*.md` (documentation)
- `tests/*` (tests)

---

## 3. Detection Rules

### Rule DRF-001: Decision→Implementation Trace

```
For every APPLIED/ACCEPTED ADR:
  → Extract key architectural claims (e.g., "single pipeline", "plugin-based")
  → Search codebase for contradicting patterns
  → Flag as Category C if contradiction found (needs ADR)
```

### Rule DRF-002: Pipeline Order Consistency

```
Verify that pipeline order documented in:
  - `docs/TECHNICAL_BASELINE.md` (section 3)
  - `kernel.py` docstring (line 5)
  - `docs/ARCHITECTURE.md` (Pipeline Data Flow)
  ARE IDENTICAL.

Deviations → Category A (align documentation)
```

### Rule DRF-003: Layer Claim Consistency

```
Verify that layer architecture claims in:
  - `docs/TECHNICAL_BASELINE.md` (section 4)
  - `docs/ARCHITECTURE.md` (Layer Diagram)
  - ADR-002 (Layer Architecture)
  ARE CONSISTENT.

Mismatched layer counts → Category A (fix header/element count)
Mismatched layer responsibilities → Category C (needs ADR)
```

### Rule DRF-004: Immutability Contract Adherence

```
Verify that files listed in `spec/IMMUTABILITY_CONTRACT.md` section 2
(CORE) have NOT been modified since the contract was established.

For every file in the immutable list:
  → Check git log for modifications after contract date
  → Flag as Category C if modified without override
```

### Rule DRF-005: Metric Consistency

```
Verify numeric claims across documents:
  - "12 Tabellen" in TECHNICAL_BASELINE.md vs actual DB table count
  - "4 Kernel Perspectives" in ARCHITECTURE.md vs actual table rows
  - Test counts across documents

Conflicting metrics → Category A (align with reality)
```

---

## 4. Output Format

```json
{
  "scanner": "drift_detector",
  "findings": [
    {
      "id": "DRF-002",
      "sources": [
        "kernel.py:5",
        "docs/TECHNICAL_BASELINE.md:30-38"
      ],
      "drift": "Pipeline order reversed: docstring shows MKC→RAG, baseline shows RAG→MKC",
      "category": "A",
      "resolution": "Align kernel.py docstring with TECHNICAL_BASELINE.md"
    }
  ]
}
```

---

## 5. Integration

| Hook Point | Action |
|-----------|--------|
| Major Release | Full drift scan before release |
| ADR Change | Scan impacted area after ADR update |
| CI/CD | Drift detection on release branches |
