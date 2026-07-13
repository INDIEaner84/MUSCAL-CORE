# GOVERNANCE RECONCILIATION REPORT
**Generated:** 2026-07-13
**Session:** S-2026-07-12-006

---

## 1. Dokument-Code-Drift

- ✅ No drift detected between write_guard.py and IMMUTABILITY_CONTRACT.md

## 2. Session Handover Coverage

- ⚠️ Session S-2026-07-11-001 in registry but has no HANDOVER file
- ⚠️ Session S-2026-07-11-002 in registry but has no HANDOVER file
- ⚠️ Session S-2026-07-12-001 in registry but has no HANDOVER file
- ⚠️ Session S-2026-07-12-002 in registry but has no HANDOVER file
- ⚠️ Session S-2026-07-12-003 in registry but has no HANDOVER file
- ⚠️ Session S-2026-07-12-004 in registry but has no HANDOVER file
- ⚠️ Session S-2026-07-12-005 in registry but has no HANDOVER file
- ⚠️ Session ** in HANDOVER but not in SESSION_REGISTRY

## 3. Commit → Session Traceability

- ⚠️ **UNTRACED_COMMIT**: Commit eb3f851 ('MUSCAL GOVERNANCE v1.1 — Technical Enforcement Lay') not found in any HANDOVER or CHANGE_JOURNAL
- ⚠️ **UNTRACED_COMMIT**: Commit 8fb860b ('MUSCAL CORE — Governance Layer v1.0') not found in any HANDOVER or CHANGE_JOURNAL

## 4. Governance Files Status

| File | Status |
|------|--------|
| guards/governance_validator.py | ✅ Present |
| guards/governance_evidence.py | ✅ Present |
| guards/governance_reconciliation.py | ✅ Present |
| guards/pre_commit_hook.py | ✅ Present |
| guards/write_guard.py | ✅ Present |
| spec/OVERRIDE.md | ✅ Present |
| docs/LOCK_PROTOCOL.md | ✅ Present |
| docs/TASK_BOARD.md | ✅ Present |
| docs/CHANGE_JOURNAL.md | ✅ Present |
| docs/SESSION_REGISTRY.md | ✅ Present |
| .opencode/SESSION_RULES.md | ✅ Present |
| .github/workflows/governance-check.yml | ✅ Present |

## Summary

- Checks passed: 1
- Issues found: 10
- Governance files: 12/12 present
- Governance maturity: 12/12