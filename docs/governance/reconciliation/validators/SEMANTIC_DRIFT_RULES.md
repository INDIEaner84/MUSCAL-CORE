# Semantic Drift Rules

**Version:** 1.0
**Status:** Specification

---

## Rule Set: SDR-IR

| Rule ID | Rule | Severity | Category | Auto-Fixable |
|---------|------|----------|----------|--------------|
| SDR-IR-001 | Pipeline order must be consistent across all docs and code | High | A | Yes |
| SDR-IR-002 | Layer count must be consistent across architecture docs | High | A | Yes |
| SDR-IR-003 | Numeric claims must match actual measurements | High | A | Yes |
| SDR-IR-004 | ADR status in PROJECT_STATE.md must match ADR-INDEX.md | High | A | Yes |
| SDR-IR-005 | Immutable files must not show post-contract modifications | Critical | C | No |
| SDR-IR-006 | Feature descriptions in docs must match actual feature implementations | Medium | B | No |
| SDR-IR-007 | Test coverage claims must match actual test files | Medium | B | No |

---

## Rule Details

### SDR-IR-001: Pipeline Order Consistency

The pipeline order: `RAG → MKC → Bridge → Optimizer → MEL → Feedback → Memory`
must be identical in:
- `kernel.py` docstring
- `docs/TECHNICAL_BASELINE.md` section 3
- `docs/ARCHITECTURE.md` Pipeline Data Flow

**Detection:** Extract pipeline representation from each source, compare.

**Fix:** Update non-conforming source to match authoritative order.

---

### SDR-IR-002: Layer Count Consistency

The architecture layer count (currently 7: L0/L1 through L7) and kernel
perspectives count (currently 5) must be consistent across:
- `docs/TECHNICAL_BASELINE.md` section 4
- `docs/ARCHITECTURE.md` Layer Diagram + Kernel Perspectives table
- ADR-002

**Detection:** Count layers and perspectives in each document, compare.

**Fix:** Update header/element count to match actual content.

---

### SDR-IR-003: Numeric Accuracy

Numeric claims in documentation must reflect reality:
- Table counts vs actual database schema
- File counts vs actual filesystem
- Test counts vs actual test execution

**Detection:** Cross-reference numeric claims with actual measurements.

**Fix:** Update document to match reality.

---

### SDR-IR-004: ADR Status Alignment

ADR statuses in `docs/PROJECT_STATE.md` "Phase abgeschlossen" section must
match `spec/ADR-INDEX.md`.

**Detection:** Compare each ADR entry across both documents.

**Fix:** Update PROJECT_STATE.md to match ADR-INDEX.md.

---

### SDR-IR-005: Immutable File Invariants

Files listed in `spec/IMMUTABILITY_CONTRACT.md` section 2 must not have been
modified after the contract date without a corresponding OVERRIDE.md entry.

**Detection:** Check git log for each immutable file.

**Fix:** Requires ADR and override process (not auto-fixable).

---

### SDR-IR-006: Feature Description Accuracy

Documented feature descriptions must match actual implementation in `features/`.

**Detection:** Compare feature documentation against `features/` directory listing.

**Fix:** Update documentation or implementation (requires review).

---

### SDR-IR-007: Test Count Accuracy

Claimed test counts in documentation must match actual test files and
test runner output.

**Detection:** Count test files + test functions, compare with documented claims.

**Fix:** Update documentation or add missing tests.

---

## Integration

| Scanner | Uses Rules |
|---------|-----------|
| Drift Detector | SDR-IR-001 through SDR-IR-007 |
