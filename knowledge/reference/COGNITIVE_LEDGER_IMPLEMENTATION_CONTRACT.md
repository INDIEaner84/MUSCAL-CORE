# COGNITIVE_LEDGER_IMPLEMENTATION_CONTRACT

Sicherer Implementierungsvertrag auf Basis MINIMAL_COGNITIVE_LEDGER_SPECIFICATION.md

- Datum: 02.08.2026
- Modus: **READ ONLY** — nur Analyse, keine Codeänderung, kein Commit, keine automatische Freigabe; Human bleibt Decision Owner
- Kennzeichnung: [F] FACT (Datei:Zeile) · [I] INFERENCE · [H] HYPOTHESIS
- Basis: MINIMAL_COGNITIVE_LEDGER_SPECIFICATION.md [MCLS], COGNITIVE_LEDGER_ARCHITECTURE_REVIEW.md [CLAR], EVENT_SOURCING_INTEGRITY_ANALYSIS.md [ESIA], B2_HYBRID_MIGRATION_ANALYSIS.md [B2MA], B2_HYBRID_ARCHITECTURE_DECISION_PACKAGE.md [B2PKG], SESSION_RULES v2.0 [SR], DECISION_REGISTRY.md [REG], PROJECT_STATE.md [PST], POST_ARB_EXECUTION_PLAN.md [PAEP], Code-Stand 02.08.2026
- Status: **created, not committed (external KF layer)**

---

## 1. Reihenfolge der Änderungen (Phasen-Übersicht)

| Phase | Inhalt | Primärer Ort | Gate davor |
|-------|--------|--------------|------------|
| 1 | EventStore Schema v2 (additive Spalten) | runtime/event_store.py (Trust-Boundary) | OVERRIDE-Klassifikation; MC-TC-006-Baseline |
| 2 | Neue Event-Typen (Evidence/Decision/Agent/Governance/State-Transition/Watchdog) | features/-Plugins + additive Store-Freigaben | Phase 1 |
| 3 | Graph Projection (Rebuild-Service) | features/ (neu) | Phase 2 (Log-Vollständigkeit) |
| 4 | Snapshot/Rebuild (Kompaktion + Restore) | features/ (neu) | Phase 3 |
| 5 | Verification Integration (muscal/-Layer-Anbindung) | features/ (Adapter-Plugin) | Phase 4 + Integrationsvertrag |

- [F] Abhängigkeits-Kette: Schema (1) → Events (2) → Projektion (3) → Snapshot (4) → Verification (5) [I: MCLS §1-2; B2MA §5].
- [F] Vor Phase 1-Code nötig (nicht Teil des Vertrags): RC-1a/RC-1b-Entscheidung, RC-2 (HDR-001), RC-4a (ADR-Review) [F: RC6_MEASUREMENT_GATE_CHECKLIST; HUMAN_DECISION_INDEX:69].

---

## 2. Phasen-Detail (Dateien · Zone · D-Prüfung · Risiko · Rollback · Tests)

### Phase 1 — EventStore Schema v2

- **Betroffene Dateien:**
  - `runtime/event_store.py` — additive Spalten (aggregate_id, aggregate_type, agent_id, evidence_refs, parent_event_id, prev_hash, metadata) + schema_version=2 [I: MCLS §2]; Migrations-Muster `_migrate_add_columns` [F: runtime/event_store.py:274-303]; append-Validierung erweitern (Attributions-Pflicht später Phase 2) [I]
  - Tests: `tests/` (Migration frisch + Bestand, append, replay) [I]
- **CORE oder features/:** [I] runtime/event_store.py ist **nicht** in der AGENTS.md-CORE-Immutability-Liste (kernel.py, graph.py, event_bus.py, muscal_os.py … runtime/kernel|llm|optimizer|api|services/*) [F: AGENTS.md] — aber Teil der **MC-TC-004/006-Trust-Boundary** („SANCTIONED G2-01") [F: spec/OVERRIDE.md:1523] → Änderung ist klassifizierte Architektur-Änderung mit OVERRIDE-Dokumentation [I: SR]
- **D-006/D-020-Prüfung:** D-020 betrifft event_store.py nicht direkt (nicht CORE-Liste) [F: AGENTS.md]; D-006 erfüllt, da keine neue Logik in CORE-Dateien [I]; OVERRIDE-Eintrag für Trust-Boundary-Modifikation nötig [I: SR OVERRIDE-Pfad]
- **Risiko:** [I] mittel — Replay-Determinismus (MC-TC-006) bei INSERT-Erweiterung; DB-Migration bei parallelen Verbindungen (zwei SQLite-Verbindungen auf eine Datei [F: spec/ADRs/ADR-EVENT-001-eventstore-boundary.md:17-20])
- **Rollback:** [I] additive Spalten sind forward-kompatibel: Rollback = Spalten unbenutzt lassen (kein Drop nötig; SQLite-Drop erfordert Table-Rebuild → vermeiden); schema_version bleibt 2 (keine Downgrade-Pflicht) [I]
- **Testanforderungen:** Migrations-Tests (frische DB + Bestands-DB + idempotent-Re-Run), append mit/ohne neue Felder, Replay-Äquivalenz vor/nach, **MC-TC-006-Rerun ±0** [F: PAEP 4.3]

### Phase 2 — Neue Event-Typen

- **Betroffene Dateien:**
  - features/events/event_adapter.py [F: features/events/event_adapter.py:8-26] — Mapping für neue Typen [I]
  - features/replay/replay_service.py — Cursor-Persistenz (E-6) [F: features/replay/replay_service.py:20,84-90] [I]
  - features/monitoring/execution_watchdog.py — EventStore-append (E-7) via EventStoreAdapter [F: execution_watchdog.py:96-119; event_adapter.py:75-85] [I]
  - runtime/event_store.py — EXECUTION_FAILED in `_EXECUTION_REQUIRED_TOPICS` (E-8) [F: event_store.py:21-32]; Agent-/Attributions-Pflicht (Invariante 3) [I: MCLS §4.3]
  - **CORE-Berührung (E-1…E-5):** graph.py (NODE_UPDATED-Delta, NODE_REMOVED, PRUNING, FOCUS) [F: graph.py:103-108,133-165] — NUR via OVERRIDE (D-020) **oder** features/-Projektionsweg ohne graph.py-Änderung [I: B2MA §2]
  - Neu: features/ für Decision-/Evidence-/Governance-/Agent-Event-Erzeuger (Plugin) [H]
- **CORE oder features/:** [I] überwiegend features/ (D-006-konform); graph.py = CORE/IMMUTABLE (D-020) [F: SR]; event_store.py = Trust-Boundary (OVER RIDE-Pflicht) [F: OVERRIDE.md:1523]
- **D-006/D-020-Prüfung:** graph.py-Änderungen = D-020-Verletzung ohne OVERRIDE → zwei Wege: (a) OVERRIDE dokumentieren + `--allow-core-write`, (b) Projection-Layer in features/, der Events über public API spielt (kein graph.py-Write) [I: B2MA §4.2]; neue Plugins in features/ = D-006-konform [F: SR]
- **Risiko:** [I] hoch — größter CORE-Berührungs-Anteil aller Phasen (Event-Gaps); Doppel-Speicherung (Store + legacy events + audit_log) [F: ESIA §2.1]
- **Rollback:** [I] features/-Plugins: Deaktivierung ohne Bestands-Rückbau (Plugin-aus); graph.py-OVERRIDE: Revert auf vorherigen Zustand (kein Bestands-Daten-Umbau); neue Topics: bleiben als Daten, lesen nicht zwingend [I]
- **Testanforderungen:** Event-Vollständigkeits-Tests je Mutation (Bijektion), Negativ-Test Attributions-Pflicht (append ohne agent_id → Fehler), Watchdog-append-Test (Restart-Persistenz), **Replay-Matrix-Prüfung vor jedem neuen Topic** [F: PAEP 3.1], MC-TC-006-Rerun

### Phase 3 — Graph Projection (Rebuild-Service)

- **Betroffene Dateien:**
  - Neu: `features/graph_rebuild/` (Plugin) — Replay-basiert, Boot-Phase-K-Anbindung [F: PAEP 3.2] [I]
  - features/replay/replay_service.py — Cursor-Persistenz wirksam nutzen [I]
  - **Kein** graph.py-Write (nur public API: add_node/update_node/add_edge via graph.emit) [F: graph.py:61-108,235-239] [I]
- **CORE oder features/:** [F] features/ (D-006) [F: PAEP 3.2]; Anbindungspunkt Boot-Phase K ist dokumentierter Integrationspunkt, muss aber als klassifizierte Berührung geprüft werden [I]
- **D-006/D-020-Prüfung:** D-006 erfüllt (features/); D-020: nur public API, keine CORE-Datei-Änderung [I]
- **Risiko:** [I] mittel — Rebuild-Treue ohne Log-Vollständigkeit (Struktur ≈78 %, Zustand ≈46 % [I: STE §4]) unzureichend; deterministische Reihenfolge (Pruning ohne Marker [F: graph.py:145-158])
- **Rollback:** [I] Plugin-Deaktivierung; Rebuild-Service bleibt inaktiv, System verhält sich wie heute [I]
- **Testanforderungen:** Rebuild ≡ Zustand (E-10-Mechanismus [I: MCLS §6 G4]), deterministische Wiederholung (gleiches Log → gleicher Zustand), Boot-Integrations-Test (Phase K), Performance-Smoke (Full-Replay bei MAX_NODES/MAX_EDGES)

### Phase 4 — Snapshot/Rebuild (Kompaktion)

- **Betroffene Dateien:**
  - Neu: features/ (Snapshot-Modul) — Format: GraphState.get_snapshot()-äquivalent [F: graph.py:254-279] + store_seq-Anker + created_at + hash [H: B2MA §3.1]
  - `_load_snapshot` (muscal_os.py:391-397) ist CORE und **bleibt unverändert** — Restore-Logik läuft als features/-Plugin [I: B2MA §3.2]
- **CORE oder features/:** [F] features/ (D-006); muscal_os.py = CORE, kein Write [F: SR]
- **D-006/D-020-Prüfung:** keine CORE-Datei-Änderung; Anrufpunkt-Klassifikation (Boot-Hook) offen [I]
- **Risiko:** [I] mittel — Snapshot-Staleness (Events nach Snapshot), Snapshot-Korruption (Hash-Prüfung nötig), Konsistenz zwischen Snapshot und Store-seq
- **Rollback:** [I] Snapshot-Erstellung deaktivieren; Restore-Pfad bleibt auf Full-Replay (heutiges Verhalten) [I]
- **Testanforderungen:** Snapshot-Roundtrip (snapshot → restore → Zustand identisch), Staleness-Test (Events nach Snapshot werden eingespielt), Korruptions-Test (Hash-Fehler erkannt), Konsistenzprüfung (E-10)

### Phase 5 — Verification Integration (muscal/-Layer)

- **Betroffene Dateien:**
  - Neu: features/ (Integrations-Adapter-Plugin) — EventStore → muscal/evidence (recorder/models [F: muscal/src/muscal/evidence/]) → Verification (engine/states [F: muscal/src/muscal/verification/]) → Ergebnis als Event (execution.verification-Muster [F: event_store.py:181-272])
  - muscal/-Paket: **bleibt separat** (eigenes pyproject [F: muscal/pyproject.toml]); keine Änderung an CORE [I]
  - Integrationsvertrag CORE↔muscal/ (fehlt heute [F: STE E1.1/E1.2]) als Vertragsdokument vor Phase-5-Code [I]
- **CORE oder features/:** [F] features/ (Adapter) + externes Paket; kein CORE-Write [I]
- **D-006/D-020-Prüfung:** erfüllt, wenn muscal/ nur über Adapter-Plugin spricht und CORE-Dateien unberührt bleiben [I: B2MA §4.2]
- **Risiko:** [I] hoch — Performance (Verification-Latenz, B2PKG R3), Boundary Drift (B2PKG R2), Timeout-Semantik (Watchdog 300 s [F: execution_watchdog.py:8])
- **Rollback:** [I] Adapter-Plugin deaktivieren; muscal/ bleibt ungenutzt (heutiger Zustand) [I]
- **Testanforderungen:** End-to-End-Fluss (Claim→Evidence→Verification→Commit), Performance-Budget-Messung, Timeout-Kaskaden-Test, MC-TC-006-Replay-Matrix für neue Events, Boundary-Tests (kein muscal/-Import in CORE)

---

## 3. Änderbar vs. Immutable

### DARF geändert werden

| Element | Bedingung |
|---------|-----------|
| features/* (neu + bestehend: replay, events, monitoring, observability, boot, tool_runtime) | [F] D-006: Erweiterungen in features/ [F: SR] — uneingeschränkt, Plugin-Contract |
| runtime/event_store.py (Schema v2, Trust-Boundary) | [F] nur als klassifizierte Architektur-Änderung mit OVERRIDE-Dokumentation (MC-TC-004/006-SANCTIONED) [F: OVERRIDE.md:1523] |
| runtime/database.py (nur additive Tabellen/Spalten via vorhandene Migrations-Muster [F: runtime/database.py:101-124]) | [I] nur additiv, keine Bestands-Spalten-Änderung |
| muscal/ (eigenes Paket) | [F] unabhängig änderbar [F: muscal/pyproject.toml]; keine CORE-Imports |
| Tests, Doku (docs/audit/, KNOWLEDGE_FOUNDATION/audit/) | [F] frei (KF-Layer, ungetrackt) [I] |

### BLEIBT IMMUTABLE

| Element | Beleg | Grund |
|---------|-------|-------|
| kernel.py, graph.py, event_bus.py, muscal_os.py, main.py, config.py, schema.py, boot_manager.py, os_config.py, sphere.py, plugin_registry.py, plugin_loader.py, memory.py, mel.py, bridge.py, feedback.py, rag.py, tools.py, trace_engine.py, debugger.py, mkc*.py | [F] AGENTS.md CORE-Liste; SR D-020 | [I] D-020-CORE-Immutability; nur OVERRIDE + `--allow-core-write` [F: AGENTS.md] |
| runtime/kernel/*, runtime/llm/*, runtime/optimizer/*, runtime/api/*, runtime/services/* | [F] AGENTS.md | [I] CORE-Runtime-Subtree |
| Event-Topics-Semantik bestehender Typen (nicht hinzufügen, nicht umdeuten) | [I] | [I] Replay-/Consumer-Kompatibilität |
| Bestands-Daten (stored_events-Zeilen, events-Zeilen) | [I] | [I] Append-only-Doktrin [F: event_store.py:36-37] |
| `_load_snapshot`-Verhalten (muscal_os.py:391-397) | [F] CORE | [I] Restore als features/-Plugin statt CORE-Änderung |

- [I] Konflikt-Regel: jede Abweichung von „DARF"-Liste → STOP → ARCHITECTURE CHANGE-Klassifikation → spec/OVERRIDE.md → nur mit Flag [F: AGENTS.md VIOLATION-Sektion].

---

## 4. Produktionspfad

```
Development → Validation → MC-TC → Human Gate
```

### 4.1 Development

- [F] Umsetzung nur im Rahmen der „DARF"-Liste (§3); jede Phase als separates, in sich testbares Paket [I]
- [F] Pre-Write-Check: `guards.write_guard.validate_write(path)` vor jedem Schreibzugriff [F: AGENTS.md]
- [I] Inkubationspfad: features/-Plugins zuerst, CORE-Berührung erst nach OVERRIDE-Freigabe [I: SR D-020]

### 4.2 Validation

- [F] Test-Suite: pytest (Basis: 384-Test-Status [F: KF3_DECISION_QUEUE §RC-1]); je Phase die Testanforderungen aus §2 [I]
- [F] MC-TC-006-Rerun ±0 nach jeder EventStore-/Replay-Änderung [F: PAEP 4.3]
- [I] Zusätzliche Validierungs-Artefakte je Phase: Migrations-Protokoll, Replay-Äquivalenz-Nachweis, Rebuild-Kennzahl-Messung, Performance-Smoke [I]

### 4.3 MC-TC (Zertifizierungs-Artefakte)

- [F] Muster: MC-TC-004 (CERTIFIED), MC-TC-006 (deterministisch), MC-TC-007 (Phase H ❌ heute [F: MC-TC-007_STATUS_ZUSAMMENFASSUNG.md:67]) [F: PST]
- [I] Pro Phase ein Zertifizierungs-Artefakt im Muster der MC-TC-Reihe: Anforderung → Nachweis → Status (CERTIFIED/CONDITIONAL/FAIL) [I]
- [F] Gate-Kriterien aus MCLS §6 (G1–G10) als Zertifizierungs-Checkliste [I: MCLS §6]

### 4.4 Human Gate

- [F] Human bleibt Decision Owner für alle Freigaben (RC-1, RC-2, RC-4a, MC-TC-005) [F: HUMAN_DECISION_INDEX:14-18,76]
- [I] Ablauf: je Phase Zertifizierungs-Artefakt → Human-Gate (Annahme/Vertagung/Ablehnung) → nächste Phase [I]
- [F] Formale Re-Messung RC-6 erst nach RC-1+RC-2+RC-4a+RC-5 [F: RC6_MEASUREMENT_GATE_CHECKLIST; HUMAN_DECISION_INDEX:69]
- [I] Abbruch-Kriterium: jede Gate-Verletzung (MC-TC-006 ±0 verletzt, Rebuild-Treue ungenügend, D-020-Verstoß) stoppt die Phase, kein Weiterrollen [I]

---

## Validation

- Read-only: keine Datei verändert (außer dieser neuen), kein Commit, keine Implementierung, keine Entscheidung, keine Freigabe erteilt.
- Alle [F] mit Datei:Zeile bzw. Artefakt-Referenz; [H]-Aussagen (Phasen-Detail, Rollback-Pfade, Zertifizierungs-Ablauf) als Vertrags-Vorschlag gekennzeichnet, kein Beschluss.
- Konsistent mit MCLS/CLAR/ESIA/B2MA/B2PKG, SESSION_RULES v2.0 (D-006/D-020), DECISION_REGISTRY, PROJECT_STATE, AGENTS.md; Statuslage unverändert.

**Ende nach Erstellung** — keine weiteren Aktionen.
