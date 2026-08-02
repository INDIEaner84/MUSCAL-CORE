# ARCHITECTURE_RISK_REGISTER_UPDATE

- Datum: 02.08.2026
- Zweck: Architecture Quality Check (Task 5) als Risiko-Register-Update: MUSCAL-2.0-Unterstützung der heutigen Architektur, Migrationsrisiken, zu validierende Annahmen, gefrorene Komponenten (read-only; keine Implementierung, keine Entscheidung, keine Score-Berechnung)
- Basis: MASTER_INDEX (TF-01…07), SOURCE_OF_TRUTH_MAP (FINDING A1/A2), 16_BLOCKER_REGISTRY_FOUNDATION, ADR_REVIEW_PACKET.md, ARCHITECTURE_DECISION_IMPACT_GRAPH.md, DECISION_REGISTRY (D-010…D-014, D-032), SESSION_RULES v2.0, KF3/KF4/KF5-Artefakte
- Status: **created, not committed (external KF layer)**
- Anmerkung: Dieses Register ergänzt die bestehende Blocker-/Risiko-Landschaft (16_BLOCKER_REGISTRY, G5 R1…R3); es ersetzt nichts und stuft nichts neu ein.

---

## 1. Unterstützt die heutige Architektur MUSCAL 2.0?

| Prüffeld | Befund | Quelle |
|----------|--------|--------|
| Durable execution | EventStore/`stored_events` + ReplayService (features/replay/) + MC-TC-006 (deterministisch) — **Grundlage vorhanden**; Graph-Rebuild (P0-1) fehlt | MC-TC-004/006; MC-TC-007 Phase H |
| Hierarchisches Multi-Agenten-Modell | heutiger Single-Agent-Kernel (ADR-001 APPLIED); keine Multi-Agent-Laufzeit; ADR-024-Prinzipien nur DRAFT | ADR-022; D-001/D-010 |
| Event-driven verification | features/event_sourcing/ + MC-TC-004 CERTIFIED — **vorhanden** | D-007; D-016 |
| Agenten-Orchestrierung | keine Implementierung (D-032 Vision, CHAT_ONLY) | 05_DECISION_REGISTRY §C |
| Cognitive Kernel / signed actions | keine Implementierung; ADR-023 DRAFT; Trust-Governance-NO-GO (Auto-Approve, ZERO-Caller) | ADR-023; MC-TC-007-TRUST-GOVERNANCE |
| Compiler-Spezifikation (RFC) | ADR-025 DRAFT; MPIR-Referenz; keine RFC-Serie | ADR-025; D-013/D-014 |

**Qualitäts-Urteil (neutral, aus Evidenz):** Die **Persistenz-/Verifikations-Säule** (durable execution, event-driven verification) ist vorhanden und zertifiziert — das ist die tragfähige Basis für den D-010-Hybrid. Die **Agenten-/Governance-Säule** (Multi-Agent, Human Sovereignty, Cognitive Kernel, RFC-Process) existiert nur als Chat-basierte Entwürfe (C2) — MUSCAL 2.0 ist damit **konzeptionell vorbereitet, aber nicht getragen** von heutigem Code. (Ableitung aus ADR-022/023/024/025 + MC-TC-007, C1.)

## 2. Migrationsrisiken

| # | Risiko | Zone | Severity (Quelle) | Anmerkung |
|---|--------|------|-------------------|-----------|
| MR-1 | D-010 vs D-001: Migrationspfad Hybrid ↔ Single-Pipeline unbestimmt | ADR-022 / ADR-001 | MEDIUM (Registry §D) | Migrationsbewertung fehlt (RC-4a NOT READY) |
| MR-2 | Trust-Governance-NO-GO: Governance↔EventStore-Disconnect (ZERO-Caller-Events, Auto-Approve) | features/tools, interface_gateway, runtime | NO-GO (MC-TC-007) | signed-actions-/P5-Ansprüche (ADR-023/024) setzen Governance-Persistenz voraus |
| MR-3 | Bypass-Pfade P0-001 (`mel.py:54`), P0-002 (`permission_engine.py:47`), P0-003 (Kernel) | Kernel-Execution | P0 (MC-TC-007) | Jede Agenten-Autonomie (D-032/D-012) würde diese Pfade aktivieren |
| MR-4 | Graph-Rebuild-Lücke (P0-1): Session-/Graph-Kontinuität über Restart | Graph-OS | P0 (G5 R1 HIGH) | MUSCAL-2.0-durable-execution-Anspruch hängt an Rekonstruierbarkeit |
| MR-5 | Baseline-Dokumente stale (TECHNICAL_BASELINE/ARCHITECTURE 12.07) | Doku | ⚠️ STALE (FINDING A1) | Migrations-Entscheidungen auf veralteter Architektur-Doku |
| MR-6 | Testzahlen-Kontradiktion (0/547/812/431/384 vs. 2.869) | Test-Doku | TF-06 (MASTER_INDEX) | Fehlbasis für Gate-Entscheidungen nach Migration |
| MR-7 | ADR-Fragmentierung (4 Orte, ADR-013-Fehlbelegung) | ADR-Landschaft | TF-05 (MASTER_INDEX) | Supersession-Konfusion bei ADR-Synchronisation (Phase 2) |

## 3. Annahmen, die Validierung erfordern

| # | Annahme | Validierungsmethode | Quelle |
|---|---------|---------------------|--------|
| VA-1 | Turnier-Primärquelle (MC-015-Chat 25.07) ist beschaffbar/importierbar | Beschaffungs-Klärung (Human/ARB); Repo-Import | KF3-L-9; §RC-4 |
| VA-2 | ReplayService kann als Rebuild-Basis dienen (Topic-Abdeckung Graph-Events) | Machbarkeits-Test (read-only-Analyse der stored_events-Topics) | KF5-Map §2; MC-TC-006 |
| VA-3 | EventStore-append erzeugt keinen Replay-Drift (Watchdog-Persistenz) | MC-TC-006-Suite vor/nach Implementierung | D-009; G7-01 P0-2 |
| VA-4 | P5-Geltungsbereich (heute vs. MUSCAL 2.0) | ARB-Review-Urteil ADR-024 | ADR_REVIEW_MATRIX |
| VA-5 | D-033…035 bleiben ohne RC-1-Wirkung (entkoppelt) | G6-04-Messung bei Plan-Doc-Erstellung | KF3-M-2; G6-04 |
| VA-6 | v0.8-Zahlenbasis (Census/Reconciliation) ist verlässlich | Abgleich REPOSITORY_CENSUS vs. TC-Report; TF-06-Auflösung | MASTER_INDEX TF-02/TF-06 |
| VA-7 | HDR-002…004 können mit Evidence-Pflicht (C0/C1) starten | Auflagen-Überprüfung (Option B) | HDR-001_DECISION_RECORD §3/§6 |
| VA-8 | ADR_REVIEW_MATRIX-Inhalt (lesbar, 57 Z.) entspricht Review-Basis (KF3-L-8 sagte „leer") | Human-Klärung (KF4-Fund, offener Punkt #6) | KF4_COMPLETION_REPORT §3-6 |

## 4. Komponenten, die gefroren bleiben sollten (Freeze-Empfehlungen — keine Entscheidung, nur Risiko-Ableitung)

| Komponente | Freeze-Grund | Quelle |
|------------|--------------|--------|
| CORE-Kern (kernel.py, mel.py, graph.py, event_bus.py, main_boot.py …) | IMMUTABLE-Vertrag (D-006/D-020); jede Änderung = ARCHITECTURE CHANGE + OVERRIDE-Pfad | SESSION_RULES v2.0; IMMUTABILITY_CONTRACT |
| EventStore/Replay-Layer | MC-TC-004 CERTIFIED + MC-TC-006 deterministisch — Änderungen nur über zertifizierten Pfad (D-036: Certification als Decision Record) | D-016/D-036; MC-TC-006 |
| Baseline 470 (EXPECTED_TOTAL) | D-041-Kalibrierung; Änderung nur mit dokumentierter Kalibrierung | D-041 |
| GRAPH_OS_ARCHITECTURE_FREEZE v1.0 | Widerspruch zu MC-TC-007 („ALL P0 BLOCKERS RESOLVED" widerlegt) — Statusänderung nur durch Entscheider (RC-1-Option D: → DEPRECATED) | MC-TC-007; G7-01 |
| ADR-022…025 (DRAFT) | Keine Akzeptanzannahmen (G4.5-B2; KF-03); Status nur durch Review-Instanz | ADR_REVIEW_MATRIX Protokoll |
| D-010…D-014 (CHAT_ONLY) | G6-04: Statusänderung erst mit Repo-Evidence | 05_DECISION_REGISTRY §F |
| specs/adrs/ (F-03-Leiche) | Keine Löschung; nur Referenz-Markierung (§RC-5-Regel) | §RC-5 |

## 5. Register-Update (Delta zu 16_BLOCKER_REGISTRY)

| Neu geführte Risiken | Klasse | Quelle (dieses Update) |
|----------------------|--------|------------------------|
| MR-1…MR-7 (Migrationsrisiken §2) | Architektur-Migration | ADR-022/023/024/025; MC-TC-007; MASTER_INDEX |
| VA-1…VA-8 (zu validierende Annahmen §3) | Annahme-Validierung | KF3-L-9; MC-TC-006; KF4-Fund |
| Freeze-Komponenten §4 | Schutz-Zonen | SESSION_RULES; D-006/D-020/D-036/D-041 |
| Risikokonzentrationen (Impact-Graph §6) | Architektur-Analyse | ARCHITECTURE_DECISION_IMPACT_GRAPH |

Keine bestehende Registrierung (B1…B7, RC-1…RC-6, R1…R3, P0-1/P0-2, HDR-001, FL-01a) wird verändert — dieses Update ist additiv und read-only.

## 6. Validation

- Read-only: keine Implementierung, keine Entscheidung, keine Statusänderung, keine Freeze-Verfügung (Empfehlungs-Charakter aus Risiko-Ableitung), keine Score-Berechnung.
- Alle Befunde mit Quelle; Severity wörtlich aus Quellen (MEDIUM/NO-GO/P0/HIGH/STALE/TF-x).
- Konsistent mit KF3/KF4/KF5-Artefakten (RC-Kanten, M-2/M-3/H-1-Korrekturen unverändert).
