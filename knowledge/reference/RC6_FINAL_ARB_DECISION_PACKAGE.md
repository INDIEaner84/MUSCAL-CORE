# RC6_FINAL_ARB_DECISION_PACKAGE

- Datum: 02.08.2026
- Zweck: Finales RC-6 Decision Package aus allen vorhandenen Evidenzen — konsolidierte Entscheidungs-Matrizen, Gap-Register, HDR-001-Ebenen-Matrix, Human Decision Sheet
- Modus: **READ ONLY** — keine Codeänderung, kein Commit, keine Architekturentscheidung, keine Empfehlung als Entscheidung, keine Optionen-Auswahl
- Kennzeichnung: [F] Fact · [I] Inference · [H] Hypothesis — jede Aussage mit Quellenreferenz
- Input-Evidenz: RC6_ARCHITECTURE_DECISION_READINESS_REPORT.md, ARB_DECISION_SIMULATION_REPORT.md, STATE_TRANSITION_EVENT_ANALYSIS.md, COGNITIVE_KERNEL_AUDIT.md, MEMORY_FABRIC_AUDIT.md, INTERFACE_LAYER_AUDIT.md, DECISION_REGISTRY.md, PROJECT_STATE.md, SESSION_RULES.md (v2.0), spec/ADR-001…025
- Status: **created, not committed (external KF layer)**

---

## Quellen-Kurzreferenz

| Kürzel | Dokument | Beleg-Basis |
|--------|----------|-------------|
| [STE] | STATE_TRANSITION_EVENT_ANALYSIS.md | Code-Zeilen, §1–§5 |
| [SIM] | ARB_DECISION_SIMULATION_REPORT.md | RC-1a/1b/RC-2-Szenarien |
| [RDY] | RC6_ARCHITECTURE_DECISION_READINESS_REPORT.md | E1.x-Fakten, Risiken, Auswirkungen |
| [SR] | SESSION_RULES.md v2.0 | Autoritätskette, CORE-Immutability, D-006/D-020 |
| [REG] | DECISION_REGISTRY.md | D-001…D-042 |
| [PST] | PROJECT_STATE.md | Status, P0-Blocker, HDR-Tabelle |

---

# TEIL 1 — RC-1a EventStore / Graph Truth Model

## 1.1 Gesicherte Faktenlage (Input-Pflicht)

| # | FACT | Quelle |
|---|------|--------|
| F-1 | EventStore existiert: append-only SQLite, `stored_events`, „SINGLE CANONICAL EVENT AUTHORITY", MC-TC-004 CERTIFIED | runtime/event_store.py:37,50-67; PST:20; REG D-016 |
| F-2 | Replay existiert: ReplayService (replay_all/topic/since) + EventStore.replay, MC-TC-006 CERTIFIED (deterministisch) | features/replay/replay_service.py:22-82; PST:21; REG D-036 |
| F-3 | GraphState-Rebuild ist NICHT vollständig möglich: Struktur-Rekonstruktion ~78%, Zustand-Rekonstruktion ~46% (Modell-Kennzahl) | STE §4 (S-1…S-12) |
| F-4 | NODE_UPDATED enthält kein vollständiges Payload-Delta (nur node_id, status, confidence, execution_id) | graph.py:103-108 [F]; Produktionsbeleg kernel.py:152-156 [F] |
| F-5 | Pruning-/Delete-Events fehlen: remove_node/remove_edge/prune_graph ohne _push_event | graph.py:133-158 [F] |
| F-6 | graph.py = CORE, IMMUTABLE (D-020); Erweiterungen nur in features/ (D-006); Core-Write nur mit OVERRIDE + `--allow-core-write` | SR; REG D-006/D-020 |
| F-7 | graph→Bus-Spiegelung + Bus→Store-Persistenz aktiv (graph.node_created/updated/edge_created, execution_started/finished) | muscal_os.py:365-382, 257, 279-294 |

## 1.2 Entscheidungs-Matrix (keine Auswahl)

| Dimension | OPTION A — EventStore Single Source of Truth | OPTION B — Dual Truth (GraphState + EventStore) | OPTION C — Reconstruction Layer / CQRS Projection |
|-----------|----------------------------------------------|------------------------------------------------|-----------------------------------------------------|
| **Architektur-Konsistenz** | [I] konsistent mit F-1/F-7 (eine Wahrheit, GraphState = Projektion); D-008 (Layer-Trennung) bleibt gewahrt [F: REG D-008] | [I] zwei Autoren, Konsistenzpflicht; keine Reconciliation-Invariante im Code [F: STE I4.1-äquivalent]; D-008-Konformität prüfbar [I] | [I] explizite Schicht zwischen EventStore und GraphState (CQRS-Projection-Muster); D-008-konform [I]; Abgrenzung zu ReplayService nötig [I] |
| **Aktueller Implementierungsgrad** | [F] Basisteile vorhanden: EventStore (F-1), Replay (F-2), `_replaying`-Flag in graph.py:56,226; fehlend: Rebuild-Service, Boot-Phase-K-Integration, Event→API-Mapping [F: STE E1.17/§5] | [F] heutiger Ist-Zustand = de-facto Dual: GraphState in-memory + parallel persistierte Bus-Spiegel [F: F-7]; Konsistenz-Semantik fehlt [F: STE X-12] | [F] nicht vorhanden; Komponenten-Bausteine existieren (ReplayService, EventStoreAdapter) [F: F-2, event_adapter.py:80-85] |
| **Migration** | [I] kein Bestands-Code-Umbau (Neu-Code in features/); Daten bereits im Store (F-1); Aufwand M–L [F: DECISION_CLOSURE_PACKAGE §RC-1] | [I] kein Umbau; aber spätere Vereinheitlichung = zweite Migration; Log-Lücken (F-4/F-5) bleiben wirksam [F] | [I] wie A plus Layer-Kontrakt-Definition; Layer-API wird Migrationsanker [I] |
| **Replay-Fähigkeit** | [I] Replay (F-2) ist Eingang des Rebuild; deterministisch; MC-TC-006 bleibt Referenz [F: REG D-036] | [I] Replay existiert, aber Live-Zustand und Rebuild divergieren ohne Abgleich [I] | [I] Replay = Layer-Eingang; Layer-Tests gegen Replay-Matrix [I] |
| **Auditfähigkeit** | [I] eine append-only-Spur (stored_events) als Audit-Grundlage; event_id UNIQUE-Idempotenz [F: event_store.py:57]; CLAIM≠PROOF verankert (verified braucht receipt_id) [F: event_store.py:202-210] | [I] Audit-Spur (Store) + Live-Zustand (Graph) — Audit-Auswertung kann zwischen beiden abweichen [I] | [I] Audit über Store; Layer erzeugt nachvollziehbare Rebuild-Nachweise [I] |
| **MUSCAL-2.0-Kompatibilität** | [I] direkt kompatibel mit Turnier-Sieger „durable execution" (ADR-022 §Context) [F: ADR-022]; Migrationspfad D-010↔D-001 bleibt undefiniert [F: REG §D MEDIUM] | [I] konfliktär zur durable-Execution-Einheitsquelle; Vereinheitlichung später [I] | [I] Layer als wiederverwendbares MUSCAL-2.0-Modul (durable-Recovery-Schicht) [I] |
| **Agent-Architecture-Kompatibilität** | [I] Agenten-Sessions mit wiederherstellbarem Graph; einheitliche Wahrheitsbasis für mehrere Agenten [I]; Session/Checkpoint bleibt bei Runtime (Kernel-Audit §4) [F: COGNITIVE_KERNEL_AUDIT] | [I] Agenten können je Leseweg unterschiedliche Wahrheit sehen (Ambiguitäts-Risiko) [I] | [I] wie A; Layer-Kontrakt als stabile Agenten-Schnittstelle [I] |
| **Wartbarkeit** | [I] eine Quelle, ein Rebuild-Pfad; Rebuild-Tests wachsen (FL-01a-Fläche) [F: REG D-040; STE E-10] | [I] teuerste Variante: Doppel-Buchführung, Drift-Diagnose [I] | [I] gut wartbar; Duplikationsrisiko mit ReplayService als Folgepflege [I] |
| **Risiko** | [I] mittel: Log-Lücken (F-4/F-5) limitieren Rebuild-Treue, bis E-1…E-4 entschieden; Replay-Determinismus (MC-TC-006) prüfen [F: STE §3] | [I] hoch: Konsistenz-Unbestimmtheit, kein Vergleichs-Orakel [I] | [I] mittel: wie A plus Abgrenzungs-/Overlap-Risiko [I] |

## 1.3 Querschnitts-Befunde

- [F] Alle drei Optionen halten die Core-Grenze ein, wenn Rebuild ausschließlich public GraphState-API nutzt (graph.py:61-108) [F: SR].
- [F] Log-Vollständigkeit ist die gemeinsame Abhängigkeit: F-4/F-5 betreffen A und C direkt, B nur bei Rebuild-Nutzung [F: STE §3 X-1…X-6].
- [I] „Dual Truth" ist im G7-01-Optionsraum (A/B/C/D) nicht deklarierbar — Kombinations-/Neudeklarationsfrage an den Entscheider [I: SIM RC-1a].

---

# TEIL 2 — RC-1b Watchdog Persistence

## 2.1 Ist-Zustand (FACT-Block)

| Aspekt | Befund | Quelle |
|--------|--------|--------|
| Liest EventStore | ✅ `get_cursor()` + `replay(cursor=0, limit=5000)` im Orphan-Scan | execution_watchdog.py:60-76 |
| Schreibt EventStore | ❌ kein append in `_force_fail_orphan()` | execution_watchdog.py:96-119 |
| Publiziert EventBus | ✅ `EXECUTION_FAILED` mit `verification_state="unverified"` | execution_watchdog.py:107-119 |
| Core-Kopplung | `from event_bus import EventPriority` (Core-Import) | execution_watchdog.py:97 |
| Rückkanal verfügbar | EventStoreAdapter.append_writer_event → EventStore.append (seq-Rückgabe) | event_adapter.py:80-85 |
| Folge-Finding | C03: Doppelalarme ohne Dedup-Persistenz | G7-01; REG/PA-09 |

## 2.2 Optionen-Darstellung (keine Entscheidung)

| Kriterium | A — Watchdog append direkt EventStore | B — EventBus primär, EventStore sekundär | C — neuer Monitoring Store | D — Hybrid |
|-----------|----------------------------------------|------------------------------------------|----------------------------|------------|
| Architektur-Muster | [I] Feature schreibt direkt in zertifizierte Persistenz (D-006-konform, features/monitoring/) [F: G7-01] | [I] Watchdog publiziert (wie heute); Persistenz über bestehende Bus→Store-Brücke (muscal_os.py:257,279-294) [F] | [I] eigener Kanal außerhalb EventStore (Audit-Log-artig, G7-01-Option D-Pendant) [F: G7-01] | [I] append + publish kombiniert; Dedup über Idempotenz [I] |
| `event_id UNIQUE` | [F] native Idempotenz im Store (event_store.py:57); deterministischer Key `orphan_{execution_id}` fängt Doppelappend per IntegrityError ab [I] | [I] Idempotenz nur, wenn Bus-Nachricht mit stabiler id in den Store fließt; heute uuid7 je publish [F: event_bus.py:52] | [I] store-spezifisch zu definieren [I] | [I] wie A [I] |
| `idempotency_key` | [I] `orphan_{execution_id}` als event_id → wiederholte Erkennung schlägt fehl (C03 gelöst) [I: STE E-7] | [I] Bus-Payload könnte idempotency_key tragen; Wirksamkeit hängt an Store-Seite [I] | [I] n/a [I] | [I] wie A [I] |
| CLAIM≠PROOF | [F] Watchdog-Event bleibt `verification_state="unverified"` (Claims-Charakter); Store verlangt für `verified` receipt_id (EvidenceRequiredError) [F: event_store.py:202-210] | [F] gleiche Semantik, falls Store-Pfad aktiv [F] | [I] Verifikations-Semantik separat zu modellieren [I] | [F] wie A [F] |
| MC-TC-006 Replay-Pflicht | [F] neue Topic-Events dürfen Replay-Determinismus nicht brechen — Replay-Matrix-Prüfung Voraussetzung (G7-01 Option A/B) [F: G7-01] | [F] gleiche Pflicht bei Store-Fluss [F] | [I] kein Replay-Impact (Kanal außerhalb EventStore) [I: G7-01 D] | [F] wie A [F] |
| Replayfähigkeit | [I] Orphan-Erkennungen im deterministischen Replay-Pfad; Erst-/Wiederholung unterscheidbar [I] | [I] nur bei aktivem Store-Fluss [I] | [I] nicht im Replay [I] | [I] wie A [I] |
| Auditfähigkeit | [I] Fehler-Historie überlebt Restart; durchsuchbar in stored_events [I] | [I] abhängig von Brücken-Aktivität [I] | [I] separierte Audit-Spur, eigene Formatfrage [I] | [I] wie A [I] |
| Persistenzkosten | [I] 1 Insert je Erkennung (SQLite); minimal [I] | [I] 1 Insert je Publikation (via Brücke) [I] | [I] eigene Tabelle/Datei [I] | [I] 1 Insert je Erkennung [I] |
| Core-Kopplung | [F] unverändert (Import bleibt); kein neuer Core-Import [F: execution_watchdog.py:97] | [F] unverändert [F] | [I] unverändert [I] | [F] unverändert [F] |
| Aufwand (Quellen-Skala) | [F] S (DECISION_CLOSURE_PACKAGE §RC-1) | [I] S (Brücke existiert, Anpassung Watchdog nötig) [I] | [F] S (Feature-lite, G7-01 D) | [F] S–M (inkl. Dedup, G7-01 B) |

## 2.3 Querschnitts-Befunde

- [F] Option B nutzt die bereits verdrahtete Bus→Store-Brücke (F-7), adressiert aber C03 nur mit stabiler Event-ID [I].
- [F] Option D ist die einzige Variante mit expliziter C03-Wirkung (Faktenlage G7-01: Option B adressiert als einzige C03) [F: G7-01; RC1-Brief §4].
- [I] EXECUTION_FAILED ist nicht in `_EXECUTION_REQUIRED_TOPICS` (event_store.py:21-32) — append ohne execution_id wäre technisch möglich; Watchdog hat execution_id ohnehin im Payload [F].

---

# TEIL 3 — Event Contract Gap Analysis (EVIDENCE GAP REGISTER)

| ID | Problem | Dateien | Zeilen | Auswirkung | Betroffene Architekturzone | Abhängigkeiten | Priorität | Entscheidungsstatus |
|----|---------|---------|--------|------------|----------------------------|----------------|-----------|---------------------|
| **E-1** | NODE_UPDATED ohne Payload-Delta — Payload-Updates (z. B. SYSTEM_ACTION-Ergebnisse) verlassen den Event-Verlauf | graph.py; kernel.py | graph.py:103-108; kernel.py:152-156 | Rebuild rekonstruiert veraltete Node-Payloads; Zustands-Treue bricht | CORE (graph.py, immutable) | RC-1a; D-020/OVERRIDE; Tests (test_graph.py) | **HIGH** | PENDING — Teil von RC-1a |
| **E-2** | Node-Removal-Events fehlen — remove_node() ohne Event | graph.py | 133-138 | Rebuild behält gelöschte Knoten | CORE (graph.py) | RC-1a; D-020 | **HIGH** | PENDING — Teil von RC-1a |
| **E-3** | Pruning-Events fehlen — prune_graph() entfernt älteste Knoten/Kanten ohne Marker | graph.py | 41-42, 145-158 | Rebuild ohne identische Pruning-Regel wächst über MAX_NODES/MAX_EDGES | CORE (graph.py) | RC-1a; Rebuild-Prüfregel | **HIGH** | PENDING — Teil von RC-1a |
| **E-4** | Edge-Mutationen unvollständig — EDGE_CREATED ohne payload/timestamp; remove_edge() ohne Event | graph.py | 124-128, 140-143 | Edge-Payloads/-Zeit verloren; Kanten-Löschungen unsichtbar | CORE (graph.py) | RC-1a; E-2/E-3-Schema | **MEDIUM** | PENDING — Teil von RC-1a |
| **E-5** | Focus-State-Events fehlen — set_focus() ohne Event | graph.py | 162-166 | active_focus_node nach Rebuild leer/falsch | CORE (graph.py) | RC-1a | **MEDIUM** | PENDING — Teil von RC-1a |
| **E-6** | Replay-Cursor nicht persistent — `_last_replayed_seq` flüchtig | features/replay/replay_service.py | 20, 43-44, 84-90 | Inkrementeller Rebuild ab „letztem Stand" unmöglich; nur Full-Replay | features/replay (Feature-Zone) | MC-TC-006; Rebuild-Strategie | **MEDIUM** | PENDING — Teil von RC-1a/C |
| **E-7** | Watchdog schreibt nicht in EventStore — `_force_fail_orphan()` nur publish | features/monitoring/execution_watchdog.py | 96-119 | Orphan-Erkennungen verloren; C03-Doppelalarme | features/monitoring (Feature, D-006) | RC-1b; MC-TC-006-Replay-Matrix; event_adapter.py:80-85 | **HIGH** | PENDING — Teil von RC-1b |
| **E-8** | EXECUTION_FAILED nicht in `_EXECUTION_REQUIRED_TOPICS` — kein execution_id-Schutz für dieses Topic | runtime/event_store.py | 21-32 | append ohne execution_id technisch möglich; Inkonsistenz mit anderen Execution-Topics | EventStore-Layer (runtime/) | RC-1b; Schema-Entscheidung | **LOW** | PENDING — Teil von RC-1b |
| **E-9** | Temporale Metadaten lückenhaft — Edge-Events ohne timestamp; Bus→Store nutzt msg.timestamp, Graph-Edge-Events verlieren Zeit | graph.py:124-128; event_bus.py:51-53; muscal_os.py:284-292 | graph.py:124-128; event_bus.py:17-23 | Zeitliche Kanten-Reihenfolge nur über seq ableitbar; Zeitreihen-Analysen eingeschränkt | CORE (graph.py) + EventStore-Layer | RC-1a; Temporal Reasoning (muscal/-Temporal-Konzepte) | **MEDIUM** | PENDING — Teil von RC-1a |
| **E-10** | Kein Rekonstruktions-Validierungsmechanismus — kein Test „Rebuild ≡ Event-Log" | — (fehlende Komponente); Bezug: MC-TC-007 Phase H ❌ FAIL | MC-TC-007_STATUS_ZUSAMMENFASSUNG.md:67 | Vollständigkeit/Determinismus des Rebuilds unbewiesen; Phase-H-Befund bleibt FAIL | Rebuild-Pfad (neu) + Test-Governance | RC-1a; Baseline 470 (D-041); MC-TC-006 | **HIGH** | PENDING — Teil von RC-1a; MC-TC-007 |

Register-Hinweis: Prioritätsstufen sind Klassifikation aus Evidenz (Severity der Auswirkung), keine Umsetzungs-Reihenfolge-Empfehlung [I].

---

# TEIL 4 — HDR-001 Trennung (Orthogonale Matrix)

## 4.1 Dimensionen

**Dimension A — Governance-Form:**
- **A1** bestehende Council-Struktur (HDR-001 Architecture Council; HDR-002…004 blockiert) [F: PST:112-119]
- **A2** erweiterte ARB-Struktur (ARB als permanentes Entscheidungsgremium) [H: Erweiterung, nicht im Repo deklariert]
- **A3** dezentrale Review-Struktur (Review-Instanzen mit begrenzten Mandaten) [H]
- **A4** temporäre Entscheidungsstruktur (befristetes Mandat bis Meilenstein) [H]

**Dimension B — Architekturform:**
- **B1** Evolution MUSCAL CORE (D-001-Pfad, ADR-001 APPLIED, features/-Plugins) [F: REG D-001/D-006]
- **B2** Hybrid CORE + muscal/-Package (zweigleisig: CORE-Runtime + Verification-Runtime; muscal/ existiert als Paket) [F: muscal/README; ADR-022 §Context]
- **B3** Cognitive OS Neubau (ADR-023-Muster: Intent→Goals→Context→Strategy→Planner→Runtime; ADR-022…025 DRAFT) [F: ADR-023/024/025]

## 4.2 Kombinations-Matrix (12 Felder — alle formal möglich)

| | B1 Evolution CORE | B2 Hybrid CORE + muscal/ | B3 Cognitive OS Neubau |
|--|-------------------|--------------------------|------------------------|
| **A1 Council** | ✅ möglich — Status quo, keine Strukturänderung [F] | ✅ möglich — Council bestellt Hybrid-Betrieb [I] | ✅ möglich — Council beschließt Neubau-Phase [I] |
| **A2 erweiterte ARB** | ✅ möglich — ARB übernimmt RC-Gates [H] | ✅ möglich — ARB koordiniert zwei Projekte [H] | ✅ möglich — ARB als Neubau-Sponsor [H] |
| **A3 dezentrale Review** | ✅ möglich — Review-Instanzen je Feature [H] | ✅ möglich — je Projekt eine Review-Instanz [H] | ✅ möglich — Layer-Review-Teams [H] |
| **A4 temporär** | ✅ möglich — befristete P0-Entscheidungsfrist [H] | ✅ möglich — befristeter Integrationsauftrag [H] | ✅ möglich — befristete Design-Phase [H] |

[I] Alle 12 Kombinationen sind formal unabhängig wählbar; keine Kombination ist durch vorhandene Dokumente ausgeschlossen. [F] Der G7-02/HDR-001-Optionsraum (A–D Governance) deckt nur die Annahme-Form ab, nicht Dimension B [F: HDR-001_DECISION_RECORD §3].

## 4.3 Abhängigkeiten

| Kombination | Abhängigkeit | Quelle |
|-------------|--------------|--------|
| B2/B3 (jede A-Variante) | ADR-022…025-Review (RC-4a) als Design-Rahmen — heute DRAFT, NICHT GESTARTET | REG §C/D; ADR-INDEX |
| B2/B3 | Migrationspfad D-010↔D-001 (MEDIUM, undefiniert) muss geklärt werden | REG §D |
| B2 | Integrationsvertrag CORE↔muscal/ fehlt (keine Kopplung im Code) | STE E1.1/E1.2; muscal/README |
| B3 | ADR-023-Cognitive-Kernel-Detail (Engines) ist Audit-Entwurf, kein akzeptierter ADR | COGNITIVE_KERNEL_AUDIT §3; ADR-023 DRAFT |
| A1/A2 (B1) | v0.8-Manual-Autorität hängt an HDR-001 (M-0.7, TC-H3 PARTIAL) | REG §RC-2; KF3-Queue |
| A4 | Frist-Definition als Auflage (kein Deadline-Mechanismus existiert) | HDR-001_DECISION_RECORD §6-3 |
| Jede Kombination | P0-1/P0-2 sind unabhängig offen (G7-01: getrennte Entscheidungen) | G7-01; PST:43-48 |

## 4.4 Unabhängige Entscheidungen

| Entscheidung | Unabhängig von | Begründung |
|--------------|----------------|------------|
| P0-1 (RC-1a) | HDR-001 A und B | G7-01: P0-Entscheidungen getrennt von HDR [F] |
| P0-2 (RC-1b) | HDR-001 A und B | G7-01 [F] |
| Governance-Form (A1–A4) | Architekturform (B1–B3) | I4-1/RDY: orthogonal, keine implizite Kopplung [I] |
| RC-4a (ADR-022…025-Review) | RC-1a/1b | Review ist Doku-Arbeit, kein Code-Pfad [F: ARB_IMPLEMENTATION_CONTRACTS RC-4a] |
| RC-5 (Doku-Konsolidierung) | RC-1a/1b | KF3-M-2: keine automatische Abhängigkeit [F] |
| MC-TC-005-Autorisierung | HDR-001-Form | eigenständiges Zertifizierungs-Gate [F: PST:23] |

---

# TEIL 5 — FINAL HUMAN DECISION SHEET

> „Human Decision Required" — kompakte Übersicht. Keine Empfehlung, keine Gewichtung, keine automatische Wahl.

## D-01 — RC-1a: Graph-OS Event Truth Model (P0-1)

- **Entscheidung:** Welches Truth Model für Graph-OS-Zustand (Persistenz/Rekonstruktion)?
- **Optionen:** A EventStore Single Source of Truth · B Dual Truth (GraphState + EventStore) · C Reconstruction Layer / CQRS Projection (G7-01-Rahmen: A/B/C/D-Optionen deklarationspflichtig)
- **Betroffene ADRs:** ADR-006 (Graph/Sphere), ADR-011 (Verification), ADR-012 (Event-Persistence), ADR-022 (MUSCAL-2.0-Hybrid), ggf. neuer ADR für Truth Model
- **Risiken:** R1 Restart-Verlust (HIGH, offen); R2 Log-Lücken (E-1…E-5: Payload-Delta, Removals, Pruning, Focus) begrenzen Rebuild-Treue; R4 Replay-Determinismus (MC-TC-006) bei neuer Schreib-/Lesart; R9 FL-01a-Fixture-Fläche
- **Nicht entschieden:** Dual-Truth-Sonderfall (nicht im G7-01-Optionsraum); Rebuild-Validierungsmechanismus (E-10); Core-Berührung bei E-1…E-5 (D-020/OVERRIDE-Frage)
- **Konsequenz bei Vertagung:** R1 bleibt wirksam (Produktions-Restart-Risiko); MC-TC-007 Phase H bleibt ❌ FAIL; M4-K3/RC-6-Re-Messung bleibt aus; Freeze-Widerspruch bleibt unaufgelöst

## D-02 — RC-1b: Watchdog Persistence (P0-2)

- **Entscheidung:** Wie werden Orphan-Erkennungen (EXECUTION_FAILED) persistiert?
- **Optionen:** A direkter EventStore-append · B EventBus primär + EventStore sekundär · C eigener Monitoring-Store · D Hybrid (append + publish + Dedup) (G7-01-Rahmen: A/B/C/D)
- **Betroffene ADRs:** ADR-003 (Event System), ADR-011/012 (Verification/Event-Persistenz), ADR-EVENT-001 (EventStore-Boundary), ggf. ADR-042-ähnliches Record
- **Risiken:** R3 Historie-/C03-Doppelalarme (offen); R4 Replay-Doppelpersistenz (MC-TC-006-Matrix-Pflicht); D-008 (kein Verschmelzen) bei Option C
- **Nicht entschieden:** Dedup-Schlüssel-Semantik (`orphan_{execution_id}`-Vorschlag als Option); EXECUTION_FAILED-Topic-Schutz (E-8); C03-Zieldefinition
- **Konsequenz bei Vertagung:** Erkennungen überleben Restart nicht; C03 bleibt (wiederholte Alarme); Phase F bleibt ⚠️ PASS*; RC-6-Re-Messung bleibt aus

## D-03 — HDR-001 Governance-Form (RC-2)

- **Entscheidung:** Annahme-Form für HDR-001 (Architecture Council)
- **Optionen:** A annehmen ohne Auflagen · B annehmen mit Auflagen · C ablehnen/verschieben · D Teilfreigabe (HDR-002)
- **Betroffene ADRs/Doku:** D-023 (Registry), PROJECT_STATE-HDR-Tabelle, SESSION_RULES-Autoritätskette, v0.8-Manual-Autorität (TC-H3)
- **Risiken:** R6 HDR-Deadlock (HDR-002…004 blockiert, 9 Dependencies); Arbeitsplanung auf unsicherer Basis; kein Frist-Mechanismus
- **Nicht entschieden:** Architekturform (D-04) — getrennt zu behandeln; G7-02-Artefaktstatus
- **Konsequenz bei Vertagung:** Deadlock hält an; M2-Eingangsgröße ungeklärt; v0.8-Manual-Autorität ungeregelt; keine Score-Wirkung ohne formale Re-Messung

## D-04 — HDR-001 Architekturform (getrennt von D-03)

- **Entscheidung:** Richtungsdeklaration der Architekturform
- **Optionen:** B1 Evolution MUSCAL CORE · B2 Hybrid CORE + muscal/ · B3 Cognitive OS Neubau
- **Betroffene ADRs:** ADR-001 (Kernel), ADR-022…025 (DRAFT), D-010 (MUSCAL-2.0, chat-only)
- **Risiken:** R7 Richtungsbindung ohne akzeptierten Rahmen; Migrationspfad D-010↔D-001 undefiniert; B2-Integrationsvertrag fehlt
- **Nicht entschieden:** als eigenständige Frage zu deklarieren (nicht im HDR-001-Text)
- **Konsequenz bei Vertagung:** keine Richtungsbindung; MUSCAL-2.0 bleibt chat-only; keine Code-Auswirkung

## D-05 — ADR-022…025 Status (RC-4a)

- **Entscheidung:** Status je ADR (Review-Runde)
- **Optionen:** PROPOSED-final · DEPRECATED · ACCEPTED (je ADR)
- **Betroffene ADRs:** ADR-022, ADR-023, ADR-024, ADR-025
- **Risiken:** Review-Inputs fehlen (Turnier-Primärquelle, Migrationsbewertung, Security-Model, Trust-Governance-Interaktion, RFC-Process) — NOT READY; Trust-Governance-NO-GO
- **Nicht entschieden:** Review-Reihenfolge der zirkulären Verhältnisfragen (ADR-022↔023↔024)
- **Konsequenz bei Vertagung:** Design-Rahmen für B2/B3 unverbindlich; M4-K2-Wirkung bleibt aus

## D-06 — MC-TC-005 Verifikations-Layer-Autorisierung

- **Entscheidung:** Autorisierung des Verifikations-Layers
- **Optionen:** AUTHORIZED · weiterhin NOT AUTHORIZED
- **Betroffene ADRs:** ADR-011 (Verification Layer), D-007 (Verification als Plugin)
- **Risiken:** nur Vorarbeiten existieren (PST:23)
- **Nicht entschieden:** Zertifizierungs-Scope
- **Konsequenz bei Vertagung:** Status quo (NOT AUTHORIZED); kein zusätzlicher Effekt auf P0-Pfade

## D-07 — Event-Contract-Gaps (E-1…E-10)

- **Entscheidung:** Behandlung der Event-Contract-Lücken (nur relevant bei RC-1a-Codepfad bzw. RC-1b)
- **Optionen:** Gaps in Rebuild-/Watchdog-Lösung integrieren · Gaps als eigene Doku-Entscheidung dokumentieren · Vertagen
- **Betroffene ADRs:** je nach Pfad ADR-006/011/012 (Rebuild) bzw. ADR-003 (Watchdog)
- **Risiken:** unbehandelte Gaps limitieren Rebuild-Treue (E-1…E-5 HIGH); C03 bleibt bei E-7-Vertagung
- **Nicht entschieden:** Core-Berührung (E-1…E-5 → D-020/OVERRIDE) vs. features/-Projektionsweg
- **Konsequenz bei Vertagung:** Rebuild-Treue bleibt begrenzt; Validation E-10 bleibt ohne Mechanismus

---

## Validation

- Read-only: keine Datei verändert, kein Commit, keine Architekturentscheidung, keine Option ausgewählt, keine Empfehlung formuliert.
- Alle [F] mit Quellenreferenz (Datei:Zeile oder Artefakt); [I]/[H] klar getrennt; Prioritätsstufen im Gap-Register als Klassifikation gekennzeichnet.
- Konsistent mit STE/SIM/RDY (vorherige KF-Artefakte), DECISION_REGISTRY, PROJECT_STATE, SESSION_RULES v2.0; Statuslage unverändert (RC-1 PENDING HUMAN, RC-2 HUMAN REQUIRED, RC-4a NICHT GESTARTET, RC-6 ausstehend).
