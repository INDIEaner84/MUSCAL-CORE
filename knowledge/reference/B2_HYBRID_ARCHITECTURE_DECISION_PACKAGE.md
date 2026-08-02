# B2_HYBRID_ARCHITECTURE_DECISION_PACKAGE

B2-Hybrid-Architektur als ARB-Entscheidungsgrundlage

- Datum: 02.08.2026
- Rolle: Architecture Decision Package Generator
- Modus: **READ ONLY** — keine Codeänderungen, keine Commits, keine Implementierung, keine automatische Entscheidung, keine Empfehlung als Fakt
- Kennzeichnung: [F] FACT (Datei:Zeile) · [I] INFERENCE · [H] HYPOTHESIS
- Zielrichtung (Arbeitshypothese, nicht beschlossen): **B2 Hybrid** — MUSCAL CORE bleibt Execution Runtime; muscal/ wird Cognitive Integrity, Verification und Governance Layer; EventStore wird Single Source of Truth
- Ausgeschlossen (Nicht-Ziele): kein Cognitive OS Neubau (B3), kein Austausch der CORE Runtime
- Quellen: RC6_FINAL_ARB_DECISION_PACKAGE.md [PKG], EVENT_SOURCING_INTEGRITY_ANALYSIS.md [ESIA], STATE_TRANSITION_EVENT_ANALYSIS.md [STE], RC6_ARCHITECTURE_DECISION_READINESS_REPORT.md [RDY], ARB_DECISION_SIMULATION_REPORT.md [SIM], CONCEPT_EVOLUTION_MAP.md [CEM] (Architecture-Evolution-Artefakt), SESSION_RULES v2.0 [SR], DECISION_REGISTRY.md [REG], PROJECT_STATE.md [PST], Code-Stand 02.08.2026
- Status: **created, not committed (external KF layer)**

---

## Teil 1 — Executive Architecture Summary

### 1.1 Aktuelle Architektur

- [F] MUSCAL CORE ist eine laufende Runtime: Kernel-Pipeline (MKC/MEL/Bridge/Memory/RAG/Feedback in kernel.py:163-169), EventBus (in-memory, event_bus.py:26-41), EventStore (SQLite append-only, „SINGLE CANONICAL EVENT AUTHORITY", runtime/event_store.py:36-37), GraphState (in-memory, graph.py:45-57), Plugin-System (features/, SR D-006).
- [F] Drei parallele Event-Systeme: `stored_events` (EventStore), `events` (Legacy-Tabelle, WriterThread-derived, runtime/kernel/writer.py:44-46), `audit_log` (30d-Retention, features/observability/event_persistence.py:8,40-59) [F: ESIA §2.1].
- [F] muscal/ ist ein eigenständiges Python-Paket v0.1 „AI Verification Runtime" mit Modulen für claims/evidence/reality/verification/security/governance/cognitive_os/prompt_compiler/workflow/simulation/compliance/incidents/tenant/mreil [F: muscal/pyproject.toml; muscal/src/muscal/; muscal/README.md „CLAIM ≠ REALITY"].
- [F] Kein Code-Kontakt zwischen CORE und muscal/ (kein Import, keine Integration) [F: STE E1.1/E1.2; muscal/README].
- [F] Zertifizierter Trust-Core: EventStore/Replay (MC-TC-004 SANCTIONED G2-01 [F: spec/OVERRIDE.md:1523], MC-TC-006 deterministisch [F: PST]); Statuslage: MC-TC-007 Phase H ❌ FAIL, Phase F ⚠️ PASS* [F: MC-TC-007_STATUS_ZUSAMMENFASSUNG.md:67,71-76].

### 1.2 Problem der zwei Architekturwelten

- [F] Welt 1 (CORE): Real-Time-Execution-Runtime mit in-memory GraphState, Restart-Verlust (P0-1 PA-08) [F: PST:47]; Watchdog ohne EventStore-Persistenz (P0-2 PA-09) [F: PST:48; features/monitoring/execution_watchdog.py:96-119].
- [F] Welt 2 (muscal/): Verification-Runtime-Philosophie (CLAIM≠PROOF), entkoppelt vom CORE-Event-System; Konzeptregister existiert (CEM §1) [F: muscal/README; CEM].
- [I] Die Welten teilen keine Zustände, keine Events und kein Governance-Modell; dadurch doppelte Semantik (Audit vs. Verification) und fehlende durchgängige Beweis-Kette [I: STE I4.1-äquivalent; ESIA §9].
- [F] Konsolidierungs-Druck: drei Event-Speicher ohne Konsistenz-Invariant [F: ESIA §2.1]; zwei Richtungs-ADR (B2 vs. B3) ohne Status [F: ADR-022 DRAFT, ADR-023 DRAFT; REG §C].

### 1.3 Warum B2 eine Integrationsarchitektur ist

- [I] B2 definiert **Verantwortlichkeits-Zuordnung** (CORE = Execution, muscal/ = Integrity/Verification/Governance, EventStore = Truth) — nicht den Austausch von Komponenten [I: Teil 2].
- [I] Integrationsanker ist der EventStore: beide Welten hängen an einer append-only-Spur (Replay/Audit/Rekonstruktion) [I: ESIA §2; PKG Teil 1].
- [F] B2 nutzt vorhandene Zertifizierungen (MC-TC-004/006) statt sie zu verwerfen [F: PST; spec/OVERRIDE.md:1523].
- [I] B2 ist kompatibel mit „durable execution"-Sieger ADR-022-Kontext [I: PKG Teil 1; ADR-022].

### 1.4 Abgrenzung zu B3 Neubau

- [F] B3 = Cognitive OS Neubau auf ADR-023-Muster (Intent→Goals→Context→Strategy→Planner→Runtime), ADR-022…025 DRAFT, NICHT GESTARTET (RC-4a NOT READY) [F: ADR-INDEX; HUMAN_DECISION_INDEX:17,51].
- [I] B2 erhält die bestehende Runtime und deren Zertifizierungen; B3 würde Trust-Core-Neubau erfordern [I: PKG Teil 5 D-05; ADR_IMPLEMENTATION_CONTRACTS].
- [H] B2 schließt B3 nicht dauerhaft aus, sondern staffelt: B2 als Übergangs- und Integrationspfad, B3 als spätere, separat zu entscheidende Richtung [H].

---

## Teil 2 — Architecture Boundary Definition

### 2.1 MUSCAL CORE (Execution Runtime)

| Verantwortlichkeit | Beleg |
|--------------------|-------|
| Kernel Pipeline (MKC/MEL/Bridge/Memory/RAG/Feedback) | [F] kernel.py:163-169 |
| RAG | [F] kernel.py:168 (RAGModule) |
| Memory | [F] kernel.py:167 (MemoryModule) |
| Runtime (SystemRuntime, ToolRuntime, Execution) | [F] muscal_os.py:347-359; features/tool_runtime/ |
| Plugin Execution (features/-Plugin-Contract) | [F] SR D-006; plugin_registry/plugin_loader |

- [I] CORE bleibt Owner der Ausführung und der Graph-Zustands-Projektion; keine Verification-/Governance-Verantwortung [I: SR; ADR-011].
- [F] CORE ist IMMUTABLE (kernel.py, graph.py, event_bus.py, muscal_os.py …) [F: SR; AGENTS.md CORE-Liste].

### 2.2 muscal/ Layer (Cognitive Integrity / Verification / Governance)

| Verantwortlichkeit | Beleg |
|--------------------|-------|
| Agent Governance (Policy Layer) | [F] muscal/src/muscal/governance/ |
| Verification (CLAIM≠PROOF) | [F] muscal/src/muscal/verification/, claims/, reality/; README „CLAIM ≠ REALITY" |
| State Machines (Verification-Zustände UNKNOWN→CLAIMED→CHECKING→VERIFIED) | [F] muscal/README |
| Evidence Management | [F] muscal/src/muscal/evidence/ |
| Policy Layer | [F] muscal/src/muscal/governance/, security/ |

- [I] muscal/ wird eingebunden als Verification-/Governance-Layer **über** dem EventStore — konsumiert Events, erzeugt Evidence-Events (Verification-Ergebnisse), ohne die Execution zu ersetzen [I: muscal/README-Philosophie; ESIA §8 C-Muster].
- [F] Integrationsvertrag CORE↔muscal/ fehlt (kein Code-Kontakt) [F: STE E1.1/E1.2] — Vertrags-Definition ist Bestandteil der Entscheidungsgrundlage [I].

### 2.3 EventStore (Single Truth)

| Verantwortlichkeit | Beleg |
|--------------------|-------|
| Single Truth (append-only, event_id UNIQUE) | [F] runtime/event_store.py:36-37,57 |
| Replay (cursor-basiert, deterministisch MC-TC-006) | [F] runtime/event_store.py:305-332; PST |
| Audit (eine append-only-Spur) | [I] ESIA §8 A |
| Reconstruction (Rebuild-Service als Projection) | [H] ESIA §1.4; RC1_BRIEF (Rebuild fehlt) |

- [F] Boundary-Regel ADR-EVENT-001: ein SQLite-File, zwei append-Pfade (MuscalOS-Wildcard + WriterThread), keine zweiten Autoritäten [F: spec/ADRs/ADR-EVENT-001-eventstore-boundary.md:11-20].
- [I] Keine Vermischung: EventStore schreibt nur append; GraphState ist Projektion, kein Autor; muscal/ erzeugt Evidence-Events, mutiert keine Execution [I: D-008-Regel; PKG Teil 2].

---

## Teil 3 — Event Sourcing Target Architecture

### 3.1 Aktueller Zustand (Ist)

- [F] Mehrere Event-Systeme: EventBus (in-memory, max 50000, event_bus.py:40,54-56), EventStore (stored_events, runtime/event_store.py:50-67), Legacy-`events` (runtime/database.py:53-71), `audit_log` (30d, event_persistence.py:8,33) [F: ESIA §2.1].
- [F] GraphState ist In-Memory-Autor + Bus-Spiegel für 5 Topics (graph.node_created/updated/edge_created/execution_started/execution_finished) [F: muscal_os.py:365-382]; Bus→Store via Wildcard `_persist_to_store` [F: muscal_os.py:257,279-294]; Bus→Graph-Rückkopplung `_bridge_to_graph` [F: muscal_os.py:381,384-389].
- [F] Mutationen ohne Event: remove_node/remove_edge/prune_graph/set_focus [F: graph.py:133-165]; NODE_UPDATED ohne Payload-Delta [F: graph.py:103-108].

### 3.2 Ziel (Soll-Fluss)

```
Mutation
   ↓
EventStore (Single Truth, append-only)
   ↓
Projection (Replay/Reconstruction Layer)
   ↓
Graph / EventBus / Audit
```

- [H] Ziel-Architektur: alle State-Mutationen laufen über EventStore; GraphState, EventBus und Audit-Log sind Projektionen des gleichen Logs [H: PKG Teil 1; ESIA §1.4].
- [F] Bausteine vorhanden: EventStore.append (event_store.py:80-152), EventStore.replay (:305-332), ReplayService (features/replay/replay_service.py:22-82), `_replaying`-Flag (graph.py:56,226-229), EventStoreAdapter (features/events/event_adapter.py:75-85) [F].
- [F] Fehlende Bausteine: Rebuild-Service, Cursor-Persistenz (E-6), Snapshot (E-10), Log-Vollständigkeit (E-1…E-5, E-9) [F: ESIA §5].

### 3.3 Bewertung der bekannten Event-Lücken

| Punkt | Ist | Ziel-Einschätzung | Beleg |
|-------|-----|-------------------|-------|
| NODE_UPDATED Payload Delta | [F] kein Delta im Event (nur status/confidence/execution_id) | [I] Delta ins Event aufnehmen (E-1); CORE-Berührung → D-020/OVERRIDE oder features/-Projektionsweg | [F: graph.py:103-108; kernel.py:152-156; ESIA E-1] |
| NODE_REMOVED Events | [F] fehlen (remove_node ohne Event) | [I] Tombstone-/Remove-Event (E-2) als Voraussetzung für Rebuild-Treue | [F: graph.py:133-138; ESIA E-2] |
| Pruning Events | [F] fehlen (prune_graph ohne Event) | [I] Pruning-Marker (E-4) für deterministische Struktur-Grenzen (MAX_NODES 5000/MAX_EDGES 10000) | [F: graph.py:41-42,145-158; ESIA E-4] |
| Focus State Events | [F] fehlen (set_focus ohne Event; implizit in add_node) | [I] Focus-Event (E-5) für temporalen Zustand | [F: graph.py:84-86,162-165; ESIA E-5] |
| Watchdog Persistence | [F] liest Store, schreibt nur Bus | [I] append via EventStoreAdapter (E-7, RC-1b A/D); EXECUTION_FAILED in _EXECUTION_REQUIRED_TOPICS (E-8) | [F: execution_watchdog.py:60-76,96-119; event_store.py:21-32; ESIA E-7/E-8] |

- [I] Gemeinsame Wirkung: erst wenn E-1…E-5 geschlossen sind, erreicht die Projection die heutige Rebuild-Treue-Kennzahl überhaupt als Zielmarke (Struktur ≈78 %, Zustand ≈46 %) [I: STE §4].

---

## Teil 4 — Reconstruction Model

### 4.1 Zielformel

```
State(t) = Snapshot(t0) + Events(t0 → t)
```

- [H] Ziel: deterministische Rekonstruktion des Graph-Zustands aus Snapshot + Event-Delta; Wiederanlauf ohne Zustandsverlust (behebt P0-1 PA-08) [H: PST:47; PKG Teil 1].
- [F] Heute gilt faktisch `State(t) ≈ Events(0 → t)` (ohne Snapshot) bei eingeschränkter Vollständigkeit (E-1…E-5) [F: ESIA §4; STE §4].

### 4.2 Notwendige Komponenten (Bewertung)

| Komponente | Status heute | Notwendig für Rekonstruktion | Beleg |
|------------|--------------|------------------------------|-------|
| Event Schema Versionierung | [F] schema_version-Spalte (Default 1) | [I] ja — Schema v2-Erweiterung additiv via _migrate_add_columns-Muster | [F: event_store.py:65,274-303; ESIA §1.1] |
| sequence ordering | [F] seq AUTOINCREMENT | [F] ja — Replay ordnet nach seq (ORDER BY seq ASC) | [F: event_store.py:51,328] |
| logical time | [F] fehlt | [I] hilfreich für Monotonie unabhängig von wall-clock; heute seq erfüllt Ordnung | [I: ESIA §6] |
| causation_id | [F] vorhanden (Default '') | [I] ja für Kausal-Ketten; belegt in receipts/verifications | [F: event_store.py:61,159,192] |
| correlation_id | [F] vorhanden (Default '') | [I] ja für Korrelations-Auflösung | [F: event_store.py:60] |
| aggregate_id | [F] fehlt in stored_events (nur in legacy events) | [I] ja für zielgerichtete Rekonstruktion je Aggregat | [F: event_store.py:50-67; database.py:62; ESIA §6] |
| payload_delta | [F] fehlt (NODE_UPDATED ohne Delta) | [I] ja — E-1 als Kern für Inhalts-Rekonstruktion | [F: graph.py:103-108; ESIA E-1] |
| snapshot mechanism | [F] fehlt (kein Restore; _load_snapshot nur Existenz-Check) | [I] ja ab wachsender Historie (E-10); heute Full-Replay beherrschbar | [F: muscal_os.py:391-397; ESIA E-10, §7] |

- [F] Verification-Referenzpfad existiert: `verified` erfordert receipt_id + execution_id (EvidenceRequiredError) [F: event_store.py:202-210] — Rekonstruktion kann diesen Claim/Proof-Kontrakt übernehmen [I].
- [I] Rebuild-Validierung (E-10) ist Voraussetzung, um „State(t) = Snapshot + Events" beweisbar zu machen (MC-TC-007 Phase H bleibt bis dahin ❌ FAIL) [F: MC-TC-007:67; ESIA E-10].

---

## Teil 5 — Agent Architecture Integration

### 5.1 Migration

Von:

```
Input → Kernel → Output
```

Zu:

```
Agent → Capability → Authorization → Execution → Evidence → Verification → Commit
```

- [H] Der Ziel-Fluss ist eine Erweiterung der heutigen Kette, kein Ersatz: CORE führt die Execution aus (Kernel), muscal/ fügt Capability-/Authorization-/Evidence-/Verification-/Commit-Schritte hinzu [H: muscal/README-Philosophie; ADR-024 P1–P5-Entwurf].
- [F] Heute: Input→Kernel→Output ohne durchgängige Evidence/Verification-Stufe; Watchdog-Verification nur als `verification_state: "unverified"`-Marker im Bus-Event [F: execution_watchdog.py:107-119; ESIA §3].
- [F] Anknüpfungspunkte: store_receipt/store_verification (event_store.py:154-272), VerificationConflictError (:225-230), VerificationOrchestrator-Quelle (:252), CLAIM≠PROOF-Philosophie (muscal/README) [F].
- [I] Commit = Verification-Ergebnis + Receipt als Event-Kette im EventStore (bereits teilweise vorhanden via execution.receipt/execution.verification) [F: event_store.py:154-179,181-272; MC-TC-004-POST-REMEDIATION:361-384].
- [I] Multi-Agent-Kompatibilität: einheitliche Wahrheitsbasis über EventStore; Agent-Identität über agent_id (im MC-TC-004-Feldkatalog vorhanden) [F: MC-TC-004-POST-REMEDIATION-TRUTH-AUDIT.md:376; PKG Teil 1].
- [F] Keine Implementierung — rein beschreibende Ziel-Migration [F].

---

## Teil 6 — Vergleich Architekturvarianten

| Kriterium | A — Evolution CORE | B2 — Hybrid CORE + muscal/ | B3 — Cognitive OS Neubau |
|-----------|--------------------|----------------------------|---------------------------|
| Produktionsrisiko | [I] niedrig: additive features/-Erweiterungen; Core-Berührung nur bei Event-Gaps (D-020) | [I] mittel: Parallel-Betrieb zweier Welten; Integrationsvertrag fehlt | [I] hoch: Neubau ohne akzeptierte Rahmen (ADR-022…025 DRAFT) |
| Migration | [I] minimal (ist-Zustand de-facto A-Basis) | [I] additiv: EventStore-Truth + muscal/-Layer einbinden; kein Bestands-Umbau | [I] vollständig: Trust-Core-Neuzertifizierung |
| Architekturqualität | [I] Verbesserung der Event-Vollständigkeit; keine neue Ebene | [I] klare Verantwortlichkeits-Trennung (Teil 2); Projection-Muster | [I] hohe Design-Freiheit, ungetestet |
| Auditfähigkeit | [I] eine append-only-Spur; E-11 (Hash) offen | [I] Evidence-Events + Store = durchgängige Kette; Ketten-Hash offen | [I] neu definierbar, ohne Bestands-Evidenz |
| Zukunftsfähigkeit | [I] trägt MUSCAL-2.0 nur als Evolution (D-010 chat-only) | [I] Verification-Runtime-Philosophie komplementär; Deckung mit ADR-022-Sieger [I: ADR-022] | [I] größter Spielraum, höchste Unsicherheit |
| Aufwand | [F] S–M (G7-01-Aufwands-Skala) [F: RC1_BRIEF] | [I] M–L (Integrationsvertrag + Layer) [I] | [I] L (Design-Phase + Akzeptanz-Kaskade) [I] |
| Governance | [F] bestehende Kette + ARB-Review [F: SR] | [I] zwei-Projekt-Governance nötig (CORE-Gates + muscal/-Layer-Gates) [I] | [I] Governance-Neubau + HDR-Entscheidungen zwingend [I: PKG Teil 4] |

- [F] RC-4a (ADR-022…025-Review) ist für jede Variante Voraussetzung (NOT READY heute) [F: HUMAN_DECISION_INDEX:51].
- **Keine Siegerwahl** — Matrix ist Entscheidungsgrundlage, keine Auswahl [F: dieser Bericht].

---

## Teil 7 — Risiken B2

### R1 Event Schema Migration

- **Problem:** Schema v2-Erweiterung (aggregate_id, metadata, payload_delta, prev_hash …) berührt zertifizierte EventStore-Tabelle; Migration muss additiv/idempotent sein (Muster: `_migrate_add_columns` [F: event_store.py:274-303])
- **Auswirkung:** Bestands-Events und Replay-Determinismus (MC-TC-006) gefährdet bei nicht-additiver Migration; DB-Migrationsfehler bei parallelen Verbindungen
- **Wahrscheinlichkeit:** mittel [I]
- **Mitigation:** additive Spalten, schema_version-Inkrement, MC-TC-006-Rerun ±0 vor Produktion (POST_ARB_EXECUTION_PLAN 4.3), Backups
- **Status:** offen — Teil von RC-1a/Schema-Entscheidung

### R2 CORE/muscal Boundary Drift

- **Problem:** Verantwortlichkeits-Zuordnung (Teil 2) kann im Betrieb verwässern (muscal/ greift in Execution, CORE übernimmt Governance)
- **Auswirkung:** Doppel-Verantwortung, Verstöße gegen D-006/D-008, nicht nachvollziehbare Zustandsänderungen
- **Wahrscheinlichkeit:** mittel [I]
- **Mitigation:** Integrationsvertrag (STE E1.2-Anker), Boundary-Tests (Import-/Zugriffs-Gates), ADR-Festschreibung der Grenze
- **Status:** offen — Integrationsvertrag fehlt [F: STE E1.1/E1.2]

### R3 Performance durch Verification Layer

- **Problem:** Verification-Schritt (Evidence→Verification→Commit) fügt Latenz pro Agent-Execution hinzu
- **Auswirkung:** End-to-End-Antwortzeit steigt; Timeout-Semantik (Watchdog 300 s [F: execution_watchdog.py:8]) und Thread-Leak-Thema (MC-TC-004:558) können sich verschärfen
- **Wahrscheinlichkeit:** mittel–hoch [I]
- **Mitigation:** asynchrone Verification außerhalb des Execution-Critpath; Messung vor Rollout; Timeout-Kaskaden anpassen
- **Status:** offen — keine Messbasis vorhanden

### R4 Migration Complexity

- **Problem:** dreigeteilte Event-Landschaft (stored_events/events/audit_log) auf eine Truth zu führen; Rebuild-Service + Cursor + Snapshot fehlen
- **Auswirkung:** Migrationspfad länger als erwartet; Legacy-`events`-Tabelle bleibt Parallel-Spur bis Entscheidung
- **Wahrscheinlichkeit:** hoch [I]
- **Mitigation:** additive Migration (ESIA §1.5), Feature-freigeschaltete Projektion, schrittweises Entfernen der Legacy-Leser
- **Status:** offen — Legacy-`events` bleibt bestehen [F: runtime/kernel/writer.py:44-46]

### R5 Governance Complexity

- **Problem:** zwei Governance-Ebenen (CORE-SESSION_RULES/HDR-Kette + muscal/-Governance-Paket) + ARB-Review überlappen
- **Auswirkung:** unklare Autorität, Entscheidungs-Doppelarbeit, v0.8-Manual-Autorität weiterhin ungeregelt (TC-H3 PARTIAL [F: REG §RC-2])
- **Wahrscheinlichkeit:** mittel [I]
- **Mitigation:** klare Autoritätskette (HDR-001-Entscheidung als Voraussetzung), Layer-spezifische Gates, Audit-Trail für Governance-Entscheidungen
- **Status:** offen — RC-2 HUMAN REQUIRED [F: HUMAN_DECISION_INDEX:15]

---

## Teil 8 — ADR Auswirkungen

### Betroffene ADRs (nur Analyse, keine Erstellung)

| ADR | Status heute | B2-Auswirkung |
|-----|--------------|---------------|
| ADR-022 (MUSCAL 2.0 Hybrid) | [F] DRAFT/PROPOSED [F: ADR-INDEX] | [I] B2 ist die Konkretisierung des Hybrid-Pfads; Review nötig (RC-4a); Migrationspfad D-010↔D-001 (MEDIUM) [F: REG §D] |
| ADR-023 (Cognitive Kernel + Authoritative Runtime) | [F] DRAFT/PROPOSED [F: ADR-INDEX] | [I] B2 übernimmt nur Kernel/Execution-Teile; B3-Elemente (Neubau) bleiben ausgeschlossen — Abgrenzung im Review klären |
| ADR-024 (Agent-Architektur P1–P5) | [F] DRAFT/PROPOSED [F: ADR-INDEX] | [I] Teil 5-Fluss (Agent→…→Commit) benötigt P1–P5-Konkretisierung; Review nötig |
| ADR-025 (Cognitive Compiler + RFC-Serie) | [F] DRAFT/PROPOSED [F: ADR-INDEX] | [I] Prompts-als-Programme ist orthogonal zu B2; Scope-Abgrenzung D-013 vs D-014 (LOW) [F: ADR-INDEX] |

### Betroffene Entscheidungen

| ID | Bedeutung | B2-Auswirkung |
|----|-----------|---------------|
| D-006 | Feature-Erweiterungen in features/ [F: SR] | [F] Rebuild-/Projection-Layer und muscal/-Adapter als features/-Pfad [I: POST_ARB_EXECUTION_PLAN 3.2] |
| D-008 | EventBus/EventStore/AuditLog-Trennung [F: REG] | [I] B2-Ziel-Fluss (Mutation→Store→Projection) ist D-008-konform; audit_log als Projektion statt Parallel-Tabelle [I: PKG Teil 2] |
| D-020 | CORE Immutability [F: SR] | [F] Event-Gaps (E-1…E-5, E-9) berühren graph.py — nur via OVERRIDE oder features/-Projektionsweg [F: SR; ESIA E-1] |
| D-033…D-035 | Doku-/Roadmap-Cluster (RC-5) [F: KF3_QUEUE] | [I] B2-Entscheidung wirkt auf Roadmap-Doku; unabhängig von RC-1 entscheidbar [F: KF3-M-2-Korrektur] |
| D-042 | (Registry-Deferred-Cluster, RC-3-Kontext) [I: REG] | [I] Abgrenzung zu B2/Event-Modell-Themen im Registry prüfen [I] |

- [F] Keine ADR erstellt; keine Statusänderung [F: dieser Bericht].

---

## Teil 9 — Production Readiness Roadmap

Nur Reihenfolge, keine Zeitversprechen:

1. **Phase 1 — Event Integrity:** Event-Gaps schließen (E-1…E-5, E-9), Schema v2-Felder additiv (aggregate_id, metadata, payload_delta), Watchdog-Persistenz (E-7/E-8), Ketten-Hash-Entscheidung (E-11)
2. **Phase 2 — Replay/Reconstruction:** Cursor-Persistenz (E-6), Rebuild-/Projection-Service (features/), Snapshot-Mechanismus (E-10), Rebuild-Validierung (MC-TC-007-Phase-H-Ziel)
3. **Phase 3 — Verification Integration:** muscal/-Layer-Anbindung an EventStore (Evidence→Verification→Commit), Integrationsvertrag CORE↔muscal/, MC-TC-006-Replay-Matrix-Prüfung je neuem Event
4. **Phase 4 — Agent Governance:** Policy-/Governance-Schicht über Event-Kette, Authorization-Schritt, Governance-Gates pro Agent-Pfad
5. **Phase 5 — Multi-Agent:** agent_id-basierte Korrelation, Multi-Agent-Wahrheitsbasis, Skalierungs-/Performance-Messung

- [F] Voraussetzung vor Phase 1-Code: RC-1a/RC-1b-Entscheidung + RC-2 (HDR-001) + RC-4a (ADR-Review) [F: RC6_MEASUREMENT_GATE_CHECKLIST; HUMAN_DECISION_INDEX:69].

---

## Teil 10 — Human ARB Decision Sheet

> Nur Fragen — keine Empfehlung, keine Gewichtung, keine automatische Wahl. Human bleibt Decision Owner.

**Frage 1:** Soll B2 Hybrid als Zielarchitektur untersucht werden?
- Kontext: B2 = CORE bleibt Execution Runtime; muscal/ wird Integrity/Verification/Governance-Layer; EventStore Single Truth [F: dieser Bericht Teil 1]
- Offen: Untersuchungs-Tiefe, Ergebnis-Pflichten, Prüf-Kriterien

**Frage 2:** Soll EventStore Single Truth werden?
- Kontext: „SINGLE CANONICAL EVENT AUTHORITY" existiert [F: event_store.py:37]; Log-Lücken E-1…E-5 offen; drei Event-Speicher ohne Invariant [F: ESIA §2.1]
- Offen: Behandlungsweg der Gaps (CORE/OVERRIDE vs. features/), Schicksal von legacy-`events` und `audit_log`

**Frage 3:** Soll muscal/ als Verification/Governance Layer integriert werden?
- Kontext: muscal/ v0.1 existiert, kein Code-Kontakt [F: muscal/README; STE E1.1]; Integrationsvertrag fehlt
- Offen: Integrations-Muster (Adapter/Plugin/Event-basiert), Performance-Budget, Boundary-Regeln

**Frage 4:** Soll B3 Neubau ausgeschlossen werden?
- Kontext: B3 = Cognitive OS Neubau (ADR-023-Muster), ADR-022…025 DRAFT, RC-4a NOT READY [F: ADR-INDEX; HUMAN_DECISION_INDEX:17,51]
- Offen: Ausschluss-Frist (permanent vs. befristet), B3-Elemente in B2 (Teil-Übernahme ja/nein)

**Frage 5:** Welche ADRs benötigen Review?
- Kontext: ADR-022…025 DRAFT [F: ADR-INDEX]; RC-4a-Review-Struktur steht (G7-03) [F: HUMAN_DECISION_INDEX:51]; Input-Vervollständigung nötig (Turnier-Primärquelle, Migrationsbewertung, Security-Model, Trust-Governance, RFC-Process) [F: KF3_QUEUE §RC-4a]
- Offen: Reihenfolge, je-ADR-Entscheidung, neue ADR (z. B. EventStore Integrity & State Reconstruction Model) [I: ESIA §10]

---

## Validation

- Read-only: keine Datei verändert (außer dieser neuen), kein Commit, keine Implementierung, keine automatische Entscheidung, keine Empfehlung als Fakt formuliert.
- Alle [F] mit Datei:Zeile bzw. Artefakt-Referenz; [H]-Aussagen (Zielformel, Agent-Fluss, Roadmap-Phasen) ausdrücklich als Vorschlags-Raum gekennzeichnet.
- Konsistent mit PKG/ESIA/STE/RDY/SIM, SESSION_RULES v2.0, DECISION_REGISTRY, PROJECT_STATE, ADR-INDEX; Statuslage unverändert (RC-1 PENDING HUMAN, RC-2 HUMAN REQUIRED, RC-4a NICHT GESTARTET).
