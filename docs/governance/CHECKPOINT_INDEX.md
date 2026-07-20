# MUSCAL CORE — CHECKPOINT INDEX (MSCE)

**Zweck:** Index von Projekt-Checkpoints mit Session-Verknüpfung. Human-readable Overlay über Git-History.
**Regel:** Append-only. Git bleibt Source of Truth für tatsächlichen Zustand.
**Hinweis:** Dies ist eine Derived View. Canonical Source ist `docs/PROJECT_CHECKPOINTS.md`.

---

## Schema

| Checkpoint | Version | Date | Session ID | Git Reference | Description | Tests Pass |
|------------|---------|------|------------|---------------|-------------|------------|

---

## Git Reference Formate

| Format | Beispiel | Beschreibung |
|--------|----------|--------------|
| Commit | `abc1234` | SHA Hash (7+ Zeichen) |
| Tag | `v0.25` | Git Tag |
| Branch Point | `main@abc1234` | Branch + Referenz |

---

## Checkpoints

| Checkpoint | Version | Date | Session ID | Git Reference | Description | Tests Pass |
|------------|---------|------|------------|---------------|-------------|------------|
| 0.25 | 1.0 | 2026-07-12 | S-2026-07-12-001 | — | Category A Auto-Fixes | UNVERIFIED |
| 0.26 | 1.0 | 2026-07-12 | S-2026-07-12-002 | — | Reconciliation Engine Foundation | UNVERIFIED |
| 0.27 | 1.0 | 2026-07-12 | S-2026-07-12-003 | — | Category B Reconciliation | UNVERIFIED |
| 0.28 | 1.0 | 2026-07-12 | S-2026-07-12-004 | — | Repository Cleanup | UNVERIFIED |
| 0.29.1 | 1.0 | 2026-07-12 | S-2026-07-12-006 | — | Reconciliation Runtime Kernel | UNVERIFIED |
| 0.29.2 | 1.0 | 2026-07-12 | S-2026-07-12-006 | — | Repository Snapshot Layer | UNVERIFIED |
| 0.30 | 1.0 | 2026-07-14 | S-2026-07-14-001 | — | ScanContext Migration | UNVERIFIED |
| 0.31 | 1.0 | 2026-07-14 | S-2026-07-14-002 | — | Rule Engine Implementation | UNVERIFIED |
| 0.32 | 1.0 | 2026-07-14 | S-2026-07-14-003 | — | BrokenLinkScanner | UNVERIFIED |
| 0.33 | 1.0 | 2026-07-15 | S-2026-07-15-001 | `c6b43d6` | ADR Validator Scanner | UNVERIFIED |
| 0.34 | 1.0 | 2026-07-15 | — | `c6b43d6` | ImportValidatorScanner | UNVERIFIED |
| 0.35 | 1.0 | 2026-07-15 | — | `7e739dc` | DriftDetectorScanner | UNVERIFIED |
| 0.36 | 1.0 | 2026-07-15 | — | `d9e941e` | RfcValidatorScanner | UNVERIFIED |
| 0.37 | 1.0 | 2026-07-15 | — | — | Runner Integration | UNVERIFIED |
| 0.38 | 1.0 | 2026-07-15 | — | — | Governance Enforcement | UNVERIFIED |
| **0.40** | **—** | **—** | **—** | **—** | **Runner Integration Tests** | **PENDING** |
| **HDR-001** | **1.0** | **2026-07-20** | **S-2026-07-20-001** | **—** | **HDR-001 Decision Readiness Audit** | **N/A** |

---

## Hinweis

Checkpoints 0.34-0.38 wurden ohne Session-Handover implementiert (Commit-only).
Session-ID ist UNKNOWN für diese Checkpoints.
