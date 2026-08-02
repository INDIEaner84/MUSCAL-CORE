# 12 — Governance Operations Foundation

- Datum: 02.08.2026
- Typ: Foundation-Dokument (read-only, keine Entscheidungen, keine Statusänderungen)
- Quellen: SOURCE_OF_TRUTH_MAP (KF), ADR_CANONICAL_MAP (KF), spec/ADR-INDEX.md, SESSION_RULES v2.0 (AGENTS.md/.opencode), PROJECT_STATE.md, DECISION_REGISTRY (KF), G6 (G6-00…G6-05), G7 (G7-01…G7-04)

## 1 Purpose

Beschreibung des Governance-Operationsmodells des Repos auf Basis belegter Artefakte und Gate-Ergebnisse — Arbeitsrahmen, Entscheidungs- und Freigabepfade, Autoritätsmodell, bekannte Governance-Lücken. Keine neuen Regeln, keine neuen Entscheidungen; nur Bestandsdokumentation.

## 2 Scope

- Abgedeckte Artefakte: SESSION_RULES v2.0, PROJECT_STATE.md, ADR-INDEX.md, HDR-001_DECISION_RECORD.md, OVERRIDE.md, MC-TC-*-Arb-Protokolle, Gate-Artefakte G6/G7, DECISION_REGISTRY, ADR_CANONICAL_MAP.
- Nicht abgedeckt: Bridge-Artefakt-Governance (fehlt, siehe §8 KG-12; Doc 17 offen), interne Autoren-Prozesse außerhalb der belegten Quellen.

## 3 Governance Model

- **Gate-basiert:** Fortschritt wird über prüfbare Gates geführt (G6-00 Eingangsprüfung → G6-05, G7-01…G7-04), jedes mit Kriterien, Belegen und Empfehlung (G7: CONDITIONAL GO — Kriterien 1–5+7 erfüllt, Kriterium 6 M4>75 nicht erfüllt; G7-04).
- **Read-only-Frame:** Core-Dateien (kernel.py, mkc.py, bridge.py, memory.py, mel.py, schema.py, mkc_rules.py, config.py, event_bus.py, graph.py, feedback.py, muscal_os.py, main.py, main_boot.py, boot_manager.py, os_config.py, sphere.py, debugger.py, tools.py, rag.py, trace_engine.py, plugin_registry.py, plugin_loader.py, runtime/kernel/*, runtime/llm/*, runtime/optimizer/*, runtime/api/*, runtime/services/*) sind IMMUTABLE; neue Features als Plugins in `features/` (AGENTS.md).
- **Beleg-Pflicht:** Jede Behauptung/Statusänderung benötigt Quelle; CHAT_ONLY-Einträge (D-010…D-014, D-030…D-035) haben keine Autorität und bleiben CHAT_ONLY (DECISION_REGISTRY, KF-Charter §2).
- **Gate-Ergebnisse werden committet** (G6: 5 Commits; G7: 4 Commits, HEAD 8104485) — Governance wirksam nur mit Commit-Beleg.

## 4 Governance Artifacts

| Artefakt | Ort | Status/Inhalt (belegt) | Quelle |
|---|---|---|---|
| SESSION_RULES v2.0 | AGENTS.md → .opencode/SESSION_RULES.md | verbindliche Session-Regeln (migriert, AGENTS.md verweist) | AGENTS.md |
| PROJECT_STATE.md | docs/PROJECT_STATE.md | Zustand 20.07; P0-1/P0-2-Update 01.08 (PENDING HUMAN, RC-1) | PROJECT_STATE, G7-01 |
| ADR-INDEX | spec/ADR-INDEX.md | kanonisch (G4.5 B1); 24 registrierte + 6 historische ADRs; 13/17 akzeptiert, ADR-022…025 DRAFT | ADR-INDEX, ADR_REVIEW_MATRIX |
| ADR_CANONICAL_MAP | KNOWLEDGE_FOUNDATION/audit | 6 physische ADR-Standorte; specs/adrs/-Leiche = F-03 (offen, G6-01) | ADR_CANONICAL_MAP, G6-01 |
| HDR-001 | docs/governance/HDR-001_DECISION_RECORD.md | 20.07; HUMAN REQUIRED (RC-2); HDR-002…004 blockiert | HDR-001, G7-02 |
| G7-01-Brief | docs/audit | RC-1: P0-1/P0-2, Optionen A–D, Human/ARB-Entscheid | G7-01 |
| OVERRIDE.md | spec/OVERRIDE.md | OVERRIDE-052 aktiv (MUSCAL-2.0-Semantik); MC-TC-003B (simulation_mode) | OVERRIDE, Census |
| DECISION_REGISTRY | KNOWLEDGE_FOUNDATION/audit | D-001…D-042; Lücken D-019, D-026…D-029; D-036…D-042 neuer Bereich (G2) | DECISION_REGISTRY |
| Source-of-Truth-Kette | docs/audit/02, docs/audit/03 | Prio 1–8 (PROJECT_STATE > MC-TC > ADR-INDEX > DECISIONS > CHANGE_JOURNAL > archive > ROADMAP > CHANGELOG) | SESSION_RULES/02/03 |

## 5 Governance Lifecycle

- **G6 (29.07):** G6-00 Eingangsprüfung → 5 Gate-Artefakte committet (G6-01…G6-05); Recheck ±0 gegenüber G5.
- **G7 (30.07–01.08):** G7-01 (P0-1/P0-2-Brief), G7-02 (HDR-001), G7-03 (ADR-Review-Matrix), G7-04 (Wissen-Gate, CONDITIONAL GO); 4 Commits bis 8104485.
- **KF-Phase:** KF-00 Charter → KF-01 Map → KF-02 Source Binding (15/20 quellengebunden) → KF-03 Start Gate → KF-1 Dokumente (13 committet) → KF-1 Completion Audit (7842431, Empfehlung A).
- **Offene Gate-Nachfolger:** RC-1…RC-6 (siehe §8); Empfehlung KF-2-Start (KF1_COMPLETION_AUDIT §10).

## 6 Decision Flow

1. **Befund** (Chat/S2, Audit, Gate) → **Klassifikation** (Fehler/Konflikt/Entscheidungslücke) in KF-Quelle.
2. **Registrierung:** D-IDs in DECISION_REGISTRY (Status CHAT_ONLY/DOCUMENTED/PLANNED/IMPLEMENTED; Confidence C0–C2).
3. **ADR-Pfad:** Architektur-relevante Punkte als ADR (akzeptiert = autoritativ); ADR-022…025 DRAFT — Review steht aus (**RC-4a**, NICHT GESTARTET, G7-03); Akzeptanz nur nach Review (KF-03-Regel: keine neuen Akzeptanzannahmen in Foundation-Docs).
4. **Human-Pfad:** P0-1/P0-2 (RC-1, Optionen A–D) und HDR-001 (RC-2, Optionen A–D) — Entscheidung liegt beim Human; bis dahin Status PENDING HUMAN / HUMAN REQUIRED.
5. **Umsetzung:** Implementierung erst nach Akzeptanz/Freigabe (MC-TC-004 CERTIFIED; FL-01a-Fix RC-3 wartet ARB-Freigabe).
6. **Re-Messung:** M1–M5 erst nach RC-1/RC-2 (RC-6, G6-05/18 §2).

## 7 Authority Model

- **Rangfolge (belegt, konsistent in 02/03/07/KF-Charter):** Code > Zertifikate (MC-TC) > PROJECT_STATE > ADRs (ADR-INDEX) > Foundation-Dokumente > Manuals (M-0.6 > M-0.7 > M-ROOT) > archive.
- **Process-Regeln (SESSION_RULES v2.0/AGENTS.md)** setzen den Arbeitsrahmen (read-only Core, Plugin-Pflicht, Pre-Write-Check `guards.write_guard.validate_write`).
- **Eingriff-Regeln:** Core-Änderungen = ARCHITECTURE CHANGE → OVERRIDE.md → nur mit `--allow-core-write` (AGENTS.md VIOLATION).
- **Keine Autorität:** CHAT_ONLY-D-IDs; archive/history (Prio 6); S-2026-07-31-001 (UNKNOWN, registry-only).
- **Konfliktfall:** kanonischer ADR-INDEX gewinnt; ADR-013-Fehllabel behoben (PA-06, d5f5ce7); F-03 separat offen (G6-01).

## 8 Known Governance Gaps

| ID | Gap | Status (unverändert) | Quelle |
|---|---|---|---|
| KG-12 | Bridge-Artefakte (104 untracked) ohne Artefakt-Governance/Lesepfad-Regel | offen — Doc 17 fehlt | G7, Doc 09 G-4 |
| KG-13 | HDR-002…004 durch RC-2 blockiert | offen — HUMAN REQUIRED | HDR-001, G7-02 |
| KG-14 | ADR-022…025-Review | NICHT GESTARTET (RC-4a) | ADR_REVIEW_MATRIX, G7-03 |
| KG-15 | MC-TC-005 NOT AUTHORIZED (Scope-Grenze unbekannt) | offen | G6/G7, Doc 09 M-2 |
| KG-16 | P0-1/P0-2 (D-033…D-035-Plan-Docs) | PENDING HUMAN (RC-1) | PROJECT_STATE 01.08, G7-01 |
| KG-17 | HDR-001 (Manual-Authority) | HUMAN REQUIRED (RC-2) | PROJECT_STATE, G7-02 |
| RC-3 | FL-01a-Fix + D-042-Freigabe | ARB-Freigabe offen | GLOBAL_STATE_ARCHITECTURE_DECISION_DRAFT, G6 |
| RC-4a | ADR-022…025-Review | NICHT GESTARTET | G7-03 |
| RC-5 | D-033…D-035, v0.8-Manual, F-03, TC-H3 | offen | G6-04, Doc 03 SO-4 |
| RC-6 | Re-Messung M1–M5 | ausstehend bis RC-1/RC-2 | G6-05, Doc 18 §2 |

## 9 Validation

- Read-only eingehalten: keine Datei außerhalb der belegten KF-1.1-Audit-Korrekturen verändert, keine neuen Entscheidungen, keine ADR-Akzeptierung, keine Statusänderung, keine Re-Messung, kein Code.
- Alle Fakten mit Quelle (Artefakt + Abschnitt/Gate); keine neuen Governance-Regeln definiert; nur bestehende dokumentiert.
- GAPs außerhalb Scope: KIR-Repo-Status (RC-5), S-07-31-001-Detailinhalt (UNKNOWN), TC-L1/L2 — in Doc 19 KG-01…KG-03 referenziert.
