# MUSCAL CI Governance v1.0

**Version:** 1.0.0
**Date:** 2026-07-15
**Status:** Authoritative CI Reference

---

## 1. Executive Summary

This document defines the CI/CD governance model for MUSCAL Reconciliation. It establishes automated quality gates that compare current findings against an approved baseline, ensuring no regressions are introduced.

**Key Principles:**
- Automated baseline comparison on every push/PR
- Known findings (FP/HA/TD) pass silently
- New TRUE_POSITIVE findings block the pipeline
- Historical archive content is excluded from enforcement

---

## 2. CI Architecture

### 2.1 Workflow Structure

```
.github/workflows/muscal-validation.yml
├── reconciliation-tests        # Unit + Integration tests
├── reconciliation-pipeline     # Full reconciliation run
├── performance-benchmarks      # Performance validation
├── quality-gates               # Baseline comparison
└── lint                        # Code quality
```

### 2.2 Job Dependencies

```
reconciliation-tests
    ├── reconciliation-pipeline
    └── performance-benchmarks
            └── quality-gates
```

### 2.3 Pipeline Flow

1. **Test Phase:** Run all reconciliation tests
2. **Pipeline Phase:** Execute reconciliation engine, generate report
3. **Benchmark Phase:** Validate performance baselines
4. **Quality Gates:** Compare findings against baseline
5. **Lint:** Code quality checks

---

## 3. Quality Gate Rules

### 3.1 Baseline Comparison Logic

The `compare_baseline.py` script implements:

1. **Run reconciliation:** Execute all 5 scanners
2. **Parse baseline:** Extract known finding classifications
3. **Classify current findings:** Match against baseline
4. **Evaluate:** Determine PASS/FAIL

### 3.2 Classification Handling

| Classification | CI Behavior | Action |
|---------------|-------------|--------|
| FALSE_POSITIVE | PASS | No action required |
| HISTORICAL_ARCHIVE | PASS | No action required |
| ACCEPTED_TECHNICAL_DEBT | PASS | Deferred as planned |
| TRUE_POSITIVE | FAIL | New regression detected |
| UNKNOWN | FAIL | Unrecognized finding |

### 3.3 Pass Conditions

Pipeline passes if:
- All findings are classified as FALSE_POSITIVE, HISTORICAL_ARCHIVE, or ACCEPTED_TECHNICAL_DEBT
- No new TRUE_POSITIVE findings detected
- All 5 scanners execute successfully

### 3.4 Fail Conditions

Pipeline fails if:
- New TRUE_POSITIVE findings detected
- Scanner execution fails
- Baseline file missing
- Report file missing
- Scanner missing from execution

---

## 4. Baseline Lifecycle

### 4.1 Baseline File

**Path:** `docs/audit/MUSCAL_FINDINGS_BASELINE_v1.0.md`

**Contents:**
- All 174 findings classified
- Classification definitions
- Scanner contribution analysis
- Priority ranking
- Remediation order

### 4.2 Baseline Update Process

1. Run reconciliation: `python3 scripts/reconcile.py`
2. Analyze new findings
3. Classify each finding
4. Update baseline document
5. Commit with message: `MUSCAL: Update Findings Baseline v{VERSION}`

### 4.3 Baseline Versioning

| Version | Date | Findings | Status |
|---------|------|----------|--------|
| v1.0 | 2026-07-15 | 174 | Active |

---

## 5. Failure Conditions

### 5.1 Scanner Failures

| Condition | Error Message | Action |
|-----------|--------------|--------|
| Scanner not found | `ERROR: Missing scanners: {...}` | Check scanner registration |
| Scanner exception | `ERROR: Scanner execution failed: {...}` | Check scanner implementation |
| Import error | `ImportError: cannot import name {...}` | Check scanner module |

### 5.2 Baseline Errors

| Condition | Error Message | Action |
|-----------|--------------|--------|
| Baseline missing | `FAIL: Baseline file missing: {...}` | Create baseline document |
| Baseline parse error | `ERROR: Cannot parse baseline: {...}` | Check baseline format |
| Report missing | `FAIL: Report file missing: {...}` | Run reconciliation first |

### 5.3 New Findings

| Condition | Error Message | Action |
|-----------|--------------|--------|
| New TRUE_POSITIVE | `FAIL: New TRUE_POSITIVE findings detected:` | Classify or fix |
| Unknown finding | `FAIL: New TRUE_POSITIVE findings detected: {...} (NEW)` | Classify in baseline |

---

## 6. Artifact Handling

### 6.1 Generated Artifacts

| Artifact | Path | Trigger |
|----------|------|---------|
| Reconciliation Report | `docs/audit/reconciliation_report.md` | Every run |
| Test Results | `pytest` output | Every run |

### 6.2 Artifact Storage

- Reconciliation report uploaded as GitHub artifact
- Test results available in job logs
- Performance benchmarks recorded

### 6.3 Artifact Retention

- Reports: 90 days
- Test results: 30 days
- Artifacts: 14 days

---

## 7. Baseline Comparison Details

### 7.1 Finding Rule Extraction

The comparison script extracts rules from finding IDs:
- `BL-001_docs_...` → Rule: `BL-001`
- `ADR-CR-004_spec_...` → Rule: `ADR-CR-004`
- `IMP-IR-001_tests_...` → Rule: `IMP-IR-001`
- `SDR-IR-001_kernel_...` → Rule: `SDR-IR-001`
- `RFC-001_archive_...` → Rule: `RFC-001`

### 7.2 Known Rules

| Rule | Classification | Count |
|------|---------------|-------|
| BL-001 | TRUE_POSITIVE | 2 |
| ADR-CR-004 | ACCEPTED_TECHNICAL_DEBT | 2 |
| ADR-CR-008 | TRUE_POSITIVE | 1 |
| ADR-CR-010 | TRUE_POSITIVE | 1 |
| IMP-IR-001 | FALSE_POSITIVE | 52 |
| IMP-IR-003 | ACCEPTED_TECHNICAL_DEBT | 52 |
| SDR-IR-001 | TRUE_POSITIVE | 1 |
| SDR-IR-002 | TRUE_POSITIVE | 1 |
| SDR-IR-003 | TRUE_POSITIVE | 1 |
| RFC-001 | HISTORICAL_ARCHIVE | 18 |
| RFC-002 | HISTORICAL_ARCHIVE | 18 |

### 7.3 Exclusion Rules

- Archive files (`archive/**`) → HISTORICAL_ARCHIVE
- Test imports (pytest, yaml) → FALSE_POSITIVE
- Third-party in tests → ACCEPTED_TECHNICAL_DEBT

---

## 8. Usage

### 8.1 Local Validation

```bash
# Run reconciliation
python3 scripts/reconcile.py

# Compare against baseline
python3 scripts/compare_baseline.py

# Expected: exit code 0 (PASS)
```

### 8.2 CI Validation

Automatic on push/PR to `main` branch.

### 8.3 Manual Override

For intentional TRUE_POSITIVE introductions:
1. Update baseline document
2. Commit baseline update
3. Re-run CI

---

## 9. Governance Rules

### 9.1 What Can Change

| Item | Allowed | Process |
|------|---------|---------|
| FALSE_POSITIVE count | Yes | Update baseline |
| HISTORICAL_ARCHIVE count | Yes | Update baseline |
| ACCEPTED_TECHNICAL_DEBT count | Yes | Update baseline |
| TRUE_POSITIVE count | Blocked | Must fix or classify |

### 9.2 What Cannot Change

| Item | Allowed | Reason |
|------|---------|--------|
| Scanner logic | No | Architecture freeze |
| Rule definitions | No | Architecture freeze |
| ADR/RFC files | No | Governance rules |
| Auto-fixes | No | Manual review required |

---

**GOVERNANCE STATUS:** This CI model is active as of 2026-07-15. All reconciliation runs are validated against the baseline.

---

*CI Governance documented by MUSCAL Reconciliation Engine.*
