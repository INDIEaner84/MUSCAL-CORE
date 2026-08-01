# MUSCAL CORE — OpenCode Session Rules v2.0

> v2.0 (Phase B, PB-03, 2026-08-01): Autoritätskette erweitert (Audit-Stand,
> Engineering-Entscheidungen, Session-Handovers) + Session-Rekonstruktions-
> Checklist. Kein Inhalt entfernt; alle v1-Regeln bleiben gültig.

## Project Status

This project has a valid technical baseline.
Every session MUST read `docs/PROJECT_STATE.md` first.

## Authoritative Documents

| Priority | Document | Path |
|----------|----------|------|
| 1 | Project State | `docs/PROJECT_STATE.md` |
| 2 | Audit / Certification Status | `docs/audit/MC-TC-*.md` (neueste Wahrheit ab 27.07) |
| 3 | Technical Baseline | `docs/TECHNICAL_BASELINE.md` |
| 4 | ADRs | `spec/ADR-*.md` |
| 5 | Engineering Decisions | `docs/engineering/D-*.md` |
| 6 | Historical ADRs/RFCs | `archive/history/adrs/*`, `archive/history/rfcs/*` |
| 7 | Architecture | `docs/ARCHITECTURE.md` |
| 8 | README | `README.md` |

Historical documents have NO authority over baseline documents.

**Conflict rule:** Bei Widerspruch gilt: MC-TC-Zertifizierung (Prio 2) >
PROJECT_STATE (Prio 1 wird bei Konflikten nachgezogen, siehe D-017-Resolution
G2 §G) > Technical Baseline > ADRs > Engineering Decisions > Historisches.
Konflikte gehören dokumentiert, nicht stillschweigend aufgelöst.

## CORE IS READ-ONLY

These files are IMMUTABLE and must NOT be modified:

```
kernel.py, mkc.py, bridge.py, memory.py, mel.py, schema.py, mkc_rules.py,
config.py, event_bus.py, graph.py, feedback.py, muscal_os.py, main.py,
main_boot.py, boot_manager.py, os_config.py, sphere.py, debugger.py,
tools.py, rag.py, trace_engine.py, plugin_registry.py, plugin_loader.py

runtime/kernel/*, runtime/llm/*, runtime/optimizer/*, runtime/api/*, runtime/services/*
```

Full contract: `spec/IMMUTABILITY_CONTRACT.md`

## ALL EXTENSIONS GO TO /features/

New features MUST be implemented as plugins in `features/`.

Plugin contract: `spec/PLUGIN_API.md`

## HISTORICAL DOCUMENTS

Documents in `docs/history/` are NOT current.
They serve as reference only.

If a historical document contradicts a baseline document,
the baseline document takes precedence.

## Verification Framework

Before implementing verification features:
→ `docs/VERIFICATION_FRAMEWORK_PLAN.md` — full implementation plan
→ `docs/VERIFICATION_CONFLICT_ANALYSIS.md` — conflict analysis
→ `spec/ADR-011-verification.md` — architecture decision

Implementation rule: Plugin-only in `features/event_sourcing/`.
Core files are NOT modified.

## VIOLATION HANDLING

If a task requires core modification:

1. STOP — do not execute
2. Classify as ARCHITECTURE CHANGE
3. Document in `spec/OVERRIDE.md`
4. Only execute with `--allow-core-write` flag

**Override-Mechanik (Governance-Referenz):** Overrides stehen in
`spec/OVERRIDE.md` (Registry OVERRIDE-001…055 + Wave-Sektionen). Override-052
erlaubt ausschließlich `guards/**`, `.github/**`, `.pre-commit-config.yaml`.
Pre-Commit-Hook: `guards/pre_commit_hook.py`; da git `--allow-core-write` nicht
an Hooks weiterreicht, gilt das dokumentierte Override-Verfahren
(Hook-Validierung manuell, dann `git commit --no-verify` + Override-Notiz).

---

## SESSION HANDOVER (MANDATORY)

Every session with file changes MUST create a SESSION_HANDOVER before completion.

### SESSION_HANDOVER Template

```markdown
# SESSION_HANDOVER

**Session ID:** [S-YYYY-MM-DD-XXX]
**Date:** [YYYY-MM-DD]
**Status:** [COMPLETED / BLOCKED / ABORTED]

---

## Changed Files

| File | Category | Lock Level |
|------|----------|------------|
| [Filename] | [Core/Feature/Documentation/Infrastructure] | [0/1/2/3] |

---

## Change Category

[Description of the type of change]

---

## Open Tasks

- [ ] [Task 1]
- [ ] [Task 2]

---

## Recommended Next Action

[What should be done next]

---

## Known Risks

- [Risk 1]
- [Risk 2]
```

### Storage

SESSION_HANDOVERs are stored in `docs/session_handovers/`.
Filename: `HANDOVER_[Session_ID].md`

### Update

After creating the SESSION_HANDOVER:
1. Update `docs/SESSION_REGISTRY.md`
2. Update `docs/TASK_BOARD.md` (if new tasks emerged)
3. Git Commit with subject: "Session Handover: [Session ID]"

### Backfill-Regel (Phase B)

Fehlende Handovers werden evidenzbasiert nachgezogen (Quellen: Git-History,
`docs/audit/`-Artefakte, `docs/engineering/`, SESSION_REGISTRY). Ist eine
Session nur über die Registry belegbar, wird der Detailinhalt als UNKNOWN
markiert — keine Erfindung. Referenz: Backfill 28.–31.07 (Commit c29c8b8).

---

## SESSION RECONSTRUCTION CHECKLIST (v2.0)

Jede neue Session MUSS vor der Arbeit die folgenden 6 Punkte rekonstruieren:

| # | Frage | Primärquelle | Status-Quelle |
|---|-------|--------------|---------------|
| 1 | **Aktueller Zustand** | `docs/PROJECT_STATE.md` + `docs/audit/MC-TC-*.md` (Cert-Status) | Certification Wave 27.–30.07 |
| 2 | **Letzte Entscheidungen** | `KNOWLEDGE_FOUNDATION/audit/DECISION_REGISTRY.md` (D-001…D-042) + `docs/audit/PB02_DECISION_REGISTRY_CONSOLIDATED_D010_D035.md` | Registry + ADR-INDEX |
| 3 | **Offene Blocker** | `docs/PROJECT_STATE.md` (P0-Sektion), `docs/governance/ACTIVE_TASKS.md`, `docs/governance/WORK_QUEUE.md` | HDR-001, P0-1, P0-2, FL-01a |
| 4 | **Nächste Schritte** | `docs/session_handovers/` (letzter Handover) + `docs/governance/` | Recommended Next Action |
| 5 | **Autoritätsquellen** | diese Datei §Authoritative Documents | Prioritätskette 1–8 |
| 6 | **Verbotene Annahmen** | siehe unten §Forbidden Assumptions | — |

### Forbidden Assumptions (verbotene Annahmen)

- **NICHT annehmen**, dass `docs/PROJECT_STATE.md` ohne Audit-Abgleich aktuell
  ist (D-017-Konflikt: 20.07-State vs 31.07-Cert-Status).
- **NICHT annehmen**, dass Tests grün = Trust-Core-fehlertolerant (19 flaky
  Tests FL-01a dokumentiert, D-040 — nicht gefixt, Reihenfolge-abhängig).
- **NICHT annehmen**, dass Overrides im Code die Wahrheit abbilden
  (OVERRIDE.md wurde rekonstruiert; Regel: Registry + Guards entscheiden).
- **NICHT annehmen**, dass Chat-Entscheidungen (S2) im Repo dokumentiert sind
  (D-010…D-014, D-030…D-035: chat-only, PLANNED).
- **NICHT annehmen**, dass Kern-Dateien von Plugins importiert werden dürfen
  (Kernel bleibt unverändert — Plugin-Contract gilt).

### Continuity-Erwartung

SESSION_CONTINUITY_AUDIT-Finding 41/100 (07.2026) ist durch die Checkliste +
Backfill (PB-01) adressiert; jede Session verfehlt den Zweck, wenn die 6
Punkte nicht in der Zusammenfassung beantwortet sind.

---

## AGENTS.md Hinweis

AGENTS.md (Projekt-Root) fasst die Regeln zusammen; diese Datei ist die
vollständige Referenz. Bei Widerspruch gilt diese Datei.
