# ARB_DECISION_SIMULATION_REPORT

- Datum: 02.08.2026
- Zweck: Simulation der Auswirkungen offener Human-Entscheidungen (RC-1a, RC-1b, RC-2) — **keine Empfehlung, keine Entscheidung, nur Entscheidungsfolgen**
- Modus: **READ-ONLY** — keine Implementierung, keine ADR-Erstellung, keine Codeänderung, keine Statusänderung, keine Score-Berechnung
- Basis: KF-4 Decision Package (RC1/RC2-Briefe, HUMAN_DECISION_INDEX), KF-5 Implementation Readiness (KF5_IMPLEMENTATION_READINESS_MAP), KF-6 Decision Contracts (ARB_IMPLEMENTATION_CONTRACTS, IMPLEMENTATION_SEQUENCE_ANALYSIS, RC6_GATE_PREPARATION_MATRIX, FREEZE_POLICY_UPDATE), Architektur-Audits (COGNITIVE_KERNEL_AUDIT.md, MEMORY_FABRIC_AUDIT.md, INTERFACE_LAYER_AUDIT.md), ADR-022 (MUSCAL 2.0 Hybrid), ADR-023/024/025 (DRAFT), G7-01, DECISION_CLOSURE_PACKAGE, SESSION_RULES v2.0, Code-Befunde
- Audit-Basis-Hinweis: Als „Nemotron Audit" / „Mimo Architecture Audit" benannte Dateien existieren **nicht** im Workspace; als Audit-Quellen dienen die im Repo vorhandenen Architektur-Audits (Kernel/Memory/Interface) [F]
- Status: **created, not committed (external KF layer)**

---

## 0. Markierungs-Konvention

| Marke | Bedeutung |
|-------|-----------|
| [F] | Fact — belegt durch Quelle (Datei:Zeile / Artefakt / C0-Code) |
| [I] | Inference — Ableitung aus belegten Fakten (Modell-Logik, kein neuer Beleg) |
| [H] | Hypothesis — Annahme ohne direkten Beleg; als solche zu prüfen |

Jede Aussage trägt genau eine Marke; Fakten nennen ihre Quelle [F(Quelle)].

---

## 1. RC-1a — Graph-OS Persistenz (P0-1)

### 1.1 Faktenlage

| # | Aussage | Marke |
|---|---------|-------|
| F1 | GraphState ist rein in-memory: `nodes: dict`, `edges: list`, `_node_counter`, `active_focus_node`, `_update_stream` | [F(graph.py:45ff)] |
| F2 | Graph-Events (NODE_CREATED, EDGE_CREATED …) WERDEN in `stored_events` persistiert (EventStore-Layer) | [F(MC-TC-007_STATUS_ZUSAMMENFASSUNG.md:67)] |
| F3 | Es existiert **kein** Rücklese-/Rebuild-Code; MC-TC-007 Phase H ❌ FAIL | [F(MC-TC-007)] |
| F4 | ReplayService (replay_all/replay_topic/replay_since) existiert und ist zertifiziert (MC-TC-006, deterministisch) | [F(features/replay/replay_service.py; MC-TC-006)] |
| F5 | Boot-Matrix „Phase K" ist dokumentiert (6 Boot-Pfade), aber kein Boot-Phasen-Rebuild-Code im Repo; Boot-Wiring nur `features/boot/utr_wiring.py` | [F(MC-TC-007-Cert §Phase K; Code-Inventar)] |
| F6 | graph.py = CORE, IMMUTABLE; nur public API add_node/update_node/add_edge; Core-Write nur mit ARCHITECTURE CHANGE + OVERRIDE + `--allow-core-write` (D-020) | [F(SESSION_RULES v2.0; AGENTS.md)] |
| F7 | Erweiterungen nur als Plugins in `features/` (D-006) | [F(SESSION_RULES v2.0)] |
| F8 | Baseline 470 (D-041); MC-TC-007 Phase L-Stand 384/384 als Regressionsbasis | [F(D-041; KF5 §2.6)] |
| F9 | P0-1 = PA-08; Restart-Risiko R1 HIGH; Status PENDING HUMAN (kein DECIDED, kein DEFERRED) | [F(16_BLOCKER_REGISTRY §5/§6; G5 R1)] |
| F10 | G7-01-Optionsraum P0-1: A Rebuild-Service, B DEFERRED, C Scope-Boundary, D Roadmap MUSCAL-2.0 — Optionen sind NICHT kombinierbar erfindbar | [F(G7-01; RC1-Brief §4)] |
| F11 | Freeze-Widerspruch: GRAPH_OS_ARCHITECTURE_FREEZE v1.0 „ALL P0 BLOCKERS RESOLVED" vs. MC-TC-007-Reality | [F(GRAPH_OS_ARCHITECTURE_FREEZE_v1.0; RC1-Brief §2)] |

### 1.2 Simulations-Szenarien (Aufgaben-Definition) und Korrespondenz

Die drei Szenarien sind **Simulations-Rahmen der Aufgabe, kein neuer Optionsraum** — jede Wahl muss als G7-01-Option A/B/C/D deklariert werden [F(G7-01; ARB_IMPLEMENTATION_CONTRACTS RC-1a: „nur A/B/C/D je P0")].

| Simulations-Szenario | Definition | Korrespondenz zu G7-01 | Marke |
|----------------------|-----------|------------------------|-------|
| **A — EventStore als einzige Wahrheit** | stored_events sind die einzige Graph-State-Quelle; GraphState wird zu einer Projektion; Rebuild beim Boot ist verbindlich | ≈ G7-01 **Option A** (Rebuild-Service) mit verschärfter Single-Source-Semantik | [I] |
| **B — Dual Truth Model** | in-memory GraphState bleibt Primärquelle für die Session; EventStore persistiert parallel; zwei Wahrheiten mit Konsistenz-/Vergleichspflicht | keine exakte G7-01-Option; Teil-Kompatibilität mit C (Scope-Boundary) bei Beibehaltung der Persistenz — **Kombinationsfrage an den Entscheider** | [I] |
| **C — Neues Reconstruction Layer** | dedizierter Rekonstruktions-Layer zwischen EventStore und GraphState (explizite Schicht mit eigener Semantik, Doku, Tests) | ≈ G7-01 **Option A** (Rebuild-Plugin) als expliziter Layer; Abgrenzung zu ReplayService muss geklärt werden | [I] |

Beobachtung: A und C unterscheiden sich primär im Architektur-Ausdruck (Wahrheits-Semantik vs. Layer-Form); beide sind in `features/` D-006-konform umsetzbar [I]. B weicht vom G7-01-Optionsraum ab und erfordert eine explizite Entscheider-Deklaration [I].

### 1.3 Bewertung je Dimension

#### Architektur

| Dimension | Szenario A | Szenario B | Szenario C |
|-----------|-----------|-----------|-----------|
| Datenfluss | eine Schreibseite (EventStore) → eine Lese-/Rebuild-Seite; GraphState = Projektion | zwei Autoren (In-Memory primär, EventStore parallel) → Synchronisationspflicht | wie A, aber mit expliziter Schicht-Schnittstelle zwischen EventStore und GraphState |
| Core-Konformität | ✅ keine Core-Änderung (nur public API) [F6] | ✅ keine Core-Änderung; aber Konsistenz-Schema muss definiert werden | ✅ keine Core-Änderung; Abgrenzung Layer↔ReplayService nötig [F4] |
| Bewertung | [I] klare Herrschaftsstruktur (eine Wahrheit); nutzt zertifizierte Infrastruktur (stored_events, ReplayService) | [I] höchste Architekturkomplexität: Drift-Zustände denkbar, wenn Konsistenz nicht garantiert | [I] saubere Modularisierung; Risiko der Layer-Duplikation mit ReplayService (Overlap) |
| MUSCAL-2.0-Bezug | [I] D-010-Sieger „durable execution" [F(ADR-022 §Context)]: Single-Source passt zur durable-Persistenz-Säule | [I] Dual-Truth ist der durable-Execution-Semantik ferner; Migrationsaufwand später | [I] Layer-Konzept als MUSCAL-2.0-Modul wiederverwendbar |

#### Migration

| Dimension | Szenario A | Szenario B | Szenario C |
|-----------|-----------|-----------|-----------|
| Bestands-Code | kein bestehender Code zu ändern (Rebuild ist Neu-Code in features/) [F3] | keine Core-Änderung; Watchdog-/Reader-Anpassungen ggf. | kein bestehender Code; neue Schicht |
| Daten | stored_events existieren bereits [F2]; keine Daten-Migration nötig | Daten bleiben doppelt (In-Memory + Log) → Migrationsfrage für später | wie A |
| Aufwand (Quellen-Skala) | M–L (DECISION_CLOSURE_PACKAGE §RC-1) [F] | nicht im G7-01-Aufwandsrahmen definiert — Schätzung nur mit Entscheider-Freigabe | M–L (wie Option A, da gleiche Rebuild-Arbeit) [I] |
| Bewertung | [I] einmalige Migration: keine Altlasten, nur Hinzufügen; Rollback = Plugin-Dir entfernen (D-006-Pfad) [F(KF5 §2.7)] | [I] Migrations-Form nur teilweise reversibel (Konsistenz-Semantik präjudiziert spätere Vereinheitlichung) | [I] wie A; Schicht-API wird später zum Migrationsanker |

#### Testaufwand

| Dimension | Szenario A | Szenario B | Szenario C |
|-----------|-----------|-----------|-----------|
| Neue Suiten | Rebuild-Tests (Rekonstruktion ≡ Event-Log; Knoten-/Kanten-Anzahl; Reihenfolge) | wie A + Konsistenz-/Drift-Tests (Dual-Truth-Vergleich) | wie A + Layer-Schnittstellen-Tests (Kontrakt zwischen Layer und GraphState) |
| Regression | Baseline 470 erweitert (kalibriert, D-041); MC-TC-006 ±0 [F8] | zusätzlich MC-TC-006 (Event-Doppelpersistenz-Risiko) | wie A |
| FL-01a-Fixtures | eigene Fixtures nötig (globale Singletons, D-040) [F(KF5 §2.4)] | wie A | wie A |
| Bewertung | [I] mittel–hoch: größte neue Testfläche (Rebuild + Boot-Integration + Konsistenz) | [I] höchster: Dual-Truth verlangt Vergleichs-Orakel, die es nicht gibt (neu zu entwerfen) | [I] wie A plus Schnittstellen-Kontrakttests; Testfläche marginal größer |

#### Risiko

| Dimension | Szenario A | Szenario B | Szenario C |
|-----------|-----------|-----------|-----------|
| Replay-Determinismus | neue Rebuild-Lesart darf MC-TC-006 nicht brechen — Prüfung nötig [F4] | höheres Risiko: parallele Wahrheit erzeugt neue Event-Lesarten | wie A |
| Core-Grenze | eingehalten (public API only) [F6] | eingehalten; aber Semantik-Risiko (welche Wahrheit gilt im Konfliktfall?) | eingehalten |
| Feature-Interferenz | hoch: RC-1a + RC-1b berühren dieselbe EventStore/Replay-Zone [F(Impact-Graph §6)] | wie A plus eigene Drift-Risiken | wie A |
| Restart-Verhalten | [I] R1 (Restart-Verlust) aufgelöst — Zustand überlebensfähig | [I] R1 nur teilweise: Wiederherstellung hängt von Konsistenz des letzten Syncs ab | [I] R1 aufgelöst (wie A, wenn Layer verbindlich läuft) |
| Gesamt | [I] mittel (kontrolliert durch zertifizierte Basis) | [I] hoch (Konsistenz-Unbestimmtheit) | [I] mittel (wie A, plus Abgrenzungsrisiko ReplayService) |

#### MUSCAL 2.0-Kompatibilität

| Dimension | Szenario A | Szenario B | Szenario C |
|-----------|-----------|-----------|-----------|
| Durable Execution (Turnier-Sieger) | [I] direkt kompatibel: Single-Source = durable-State-Muster | [I] Konfliktpotenzial: Dual-Truth widerspricht durable-Execution-Einheitsquelle | [I] kompatibel (Layer = durable-Recovery-Schicht) |
| ADR-022 | Migrationspfad D-010↔D-001 bleibt undefiniert [F(ADR-022 §Migration)] — unabhängig vom Szenario | unabhängig | unabhängig |
| ADR-023/024/025 (DRAFT) | kein direkter Bezug; nur Session-State-Basis für Agenten [F(COGNITIVE_KERNEL_AUDIT §4: Session/checkpoint bleibt bei Runtime)] | kein direkter Bezug | kein direkter Bezug |
| Bewertung | [I] beste Passung zur Persistenz-Säule von MUSCAL-2.0 | [I] erzeugt späteren Vereinheitlichungsbedarf | [I] gute Passung; Layer-Kontrakt kann in MUSCAL-2.0 übernommen werden |

#### Agent Architecture

| Dimension | Szenario A | Szenario B | Szenario C |
|-----------|-----------|-----------|-----------|
| Session-Recovery | [I] Agenten-Sessions können Graph-Zustand nach Restart rekonstruieren (A-001-artige Risiken, Verifikations-Graph-Erhalt) | [I] Recovery hängt von Konsistenz ab; nicht garantiert | [I] wie A |
| Multi-Agenten-Modell (ADR-024) | [I] einheitlicher, wiederherstellbarer Graph = gemeinsame Wahrheitsbasis für mehrere Agenten | [I] Agenten sehen je nach Leseweg unterschiedliche Wahrheit (Risiko) | [I] wie A |
| Kernel-Audit (TaskContract→Intent, Goals, UnifiedContext) | kein direkter Bezug — Kernel-Struktur unberührt [F(COGNITIVE_KERNEL_AUDIT §4: Event-Persistenz bleibt EventStore)] | kein direkter Bezug | kein direkter Bezug |
| Bewertung | [I] stärkste Agent-Architektur-Folge: persistente, einheitliche Session-State | [I] schwächste: Wahrheits-Ambiguität im Agenten-Pfad | [I] wie A |

#### Langfristige Wartbarkeit

| Dimension | Szenario A | Szenario B | Szenario C |
|-----------|-----------|-----------|-----------|
| Zuständigkeit | eine Quelle → ein Rebuild-Pfad; Wartung klar lokalisiert | zwei Wahrheiten → permanente Synchronisations-Wartung | Layer-Kontrakt als stabiler Anker; Pflege der Schnittstelle |
| Wissenspfad | zertifizierte Basis (MC-TC-004/006) bleibt Referenz [F] | Doppel-Buchführung erhöht kognitive Last | wie A |
| Bewertung | [I] gut wartbar; einziges Folgeproblem: Rebuild-Tests wachsen mit FL-01a-Fläche | [I] am teuersten langfristig (Drift-Diagnose, Konflikt-Entscheidungen) | [I] gut wartbar; Achtung vor Parallelstruktur zu ReplayService |

### 1.4 Entscheidungsfolgen (je Szenario)

| Szenario | Was sich ändert | Was unverändert bleibt |
|----------|----------------|------------------------|
| A | Rebuild-Pfad entsteht; R1 wird auflösbar; MC-TC-007 Phase H wird überprüfbar (Phase-H-Befund-Update nach Umsetzung) | Status PENDING HUMAN bis Entscheidung; Gate CONDITIONAL; M4-K3-Wirkung nur via Re-Messung; P0-2 bleibt separat offen |
| B | neue Konsistenz-/Dual-Truth-Semantik (nicht im G7-01-Rahmen); R1 nur teilweise adressiert | alles oben |
| C | wie A, plus Layer-Kontrakt-Doku; Abgrenzung zu ReplayService als offene Klärung | alles oben |

Gemeinsam [F/]I]: Jede Wahl erfordert die Freeze-Widerspruch-Auflösung (F11) als Teil der Entscheidung [F(ARB_IMPLEMENTATION_CONTRACTS RC-1a: „Auflösung … nur durch Entscheider (Teil jeder Option)")]; ohne Entscheidung bleibt R1 HIGH wirksam und die formale Re-Messung (RC-6) aus [F(RC1-Brief §7)].

---

## 2. RC-1b — Watchdog Persistence (P0-2)

### 2.1 Faktenlage

| # | Aussage | Marke |
|---|---------|-------|
| F12 | `ExecutionWatchdog._force_fail_orphan()` publiziert nur `EXECUTION_FAILED` via `event_bus.publish(...)`; kein `EventStore.append()` | [F(features/monitoring/execution_watchdog.py:96-119)] |
| F13 | `EventStoreAdapter` (features/events/event_adapter.py:75-85) → EventStore.append mit seq-Rückgabe existiert | [F(Code)] |
| F14 | MC-TC-007 Phase F ⚠️ PASS* (Stern = Persistenzlücke); Folge-Finding C03 (Doppelalarme, keine Dedup-Persistenz) | [F(MC-TC-007_STATUS_ZUSAMMENFASSUNG.md:71-76; G7-01)] |
| F15 | features/monitoring/ ist NICHT CORE (Feature) — D-006-konform | [F(G7-01)] |
| F16 | G7-01-Optionen P0-2: A Persistenz, B Persistenz+Dedup (adressiert C03), C DEFERRED, D Audit-only (eigener Kanal außerhalb EventStore) | [F(G7-01; RC1-Brief §4)] |
| F17 | D-008: EventBus/EventStore/AuditLog dürfen nicht verschmelzen; D-009: append-Signatur verifiziert (Bridge-Callback-Mismatch-Historie) | [F(SESSION_RULES v2.0; KF5 §3.3)] |
| F18 | Watchdog hat Core-Import `from event_bus import EventPriority` (versteckte Kopplung an Core-Event-System) | [F(execution_watchdog.py:97; Impact-Graph §4)] |
| F19 | EXECUTION_FAILED-Topic wird im Kernel-/Verifikationspfad konsumiert | [F(Impact-Graph §4)] |

### 2.2 Bewertung je Aspekt (Simulations-Optionen = G7-01-Optionen A/B/C/D)

#### EventStore Integration

| Option | Wirkung | Marke |
|--------|---------|-------|
| A | `_force_fail_orphan()` nutzt EventStoreAdapter → EXECUTION_FAILED landet in stored_events; Replay-Relevanz (MC-TC-006-Matrix) prüfen | [I] |
| B | wie A + Dedup-Marker (C03-Lösung — einzige Option mit C03-Wirkung, Faktenlage G7-01) | [I] |
| C | keine Integration; Watchdog bleibt Session-only | [F] |
| D | kein EventStore-Topic; eigener Audit-Kanal außerhalb (kein Replay-Impact) | [F(G7-01)] |
| Querschnitt | [F17] erzwingt: Persistenz in EventStore (nicht AuditLog); append-Signatur vorab verifizieren | [F] |

#### EventBus Rolle

| Option | Wirkung | Marke |
|--------|---------|-------|
| A/B | EventBus bleibt Publikationskanal; EventStore.append ergänzt Persistenz — EventBus verliert die „einzige Wirksamkeit", gewinnt aber keinen Schreibauftrag (Rollen-Trennung D-008 bleibt) | [I] |
| C | EventBus bleibt alleiniger Kanal; keine Rollenänderung | [F] |
| D | EventBus unverändert; Audit-Schreibpfad läuft am EventBus vorbei | [I] |
| Querschnitt | Versteckte Kopplung F18 bleibt in allen Optionen (Core-Import) — keine Option entfernt sie | [F/]I] |

#### Auditfähigkeit

| Option | Wirkung | Marke |
|--------|---------|-------|
| A | Fehler-Historie überlebt Restart; Alarme reduziert; Audit über stored_events möglich | [I] |
| B | wie A + keine Doppelalarme (deduplizierte Historie) — beste Audit-Datenqualität | [I] |
| C | keine Historie; C03 bleibt (wiederholte Alarme) | [F(RC1-Brief §7)] |
| D | Historie im Log, nicht im Event-Graph; Audit-Format eigener Prägung | [F(G7-01)] |
| Querschnitt | Audit-Tiefe korreliert mit EventStore-Nutzung: A/B erzeugen durchsuchbare, versionierte Belege; D erzeugt separierte Belege ohne Replay-Wirkung | [I] |

#### Fehlermodell

| Option | Wirkung | Marke |
|--------|---------|-------|
| A | Orphan-Erkennung wird persistiert; Wiederholungserkennung erfordert Rücklese (Replay) — Fehler-Erstauftritt vs. -Wiederholung wird unterscheidbar | [I] |
| B | Dedup-Marker macht Wiederholungen identifizierbar (C03); Fehlermodell erhält eindeutige Orphan-Identität | [I] |
| C | Fehlermodell unverändert: jeder Restart kann dieselben Orphans neu melden | [F] |
| D | Fehler werden audit-seitig erfasst, aber nicht im Event-Modell; Replay sieht sie nicht | [F/]I] |
| Querschnitt | Doppelpersistenz-Risiko: Option A/B muss gegen MC-TC-006-Replay-Matrix geprüft werden, bevor sie deterministisch bleibt [F(G7-01: „Replay-Relevanz (MC-TC-006-Matrix prüfen)")] | [F] |

### 2.3 Entscheidungsfolgen

| Option | Ändert | Ändert nicht |
|--------|--------|--------------|
| A | Watchdog-Historie persistent; Phase F → voll PASS dokumentierbar; Baseline-Erweiterung; neue Persistenz-Tests | C03 (Doppelalarme) |
| B | wie A + C03; ADR-042-ähnliches Record | — |
| C | DEFERRED-Markierung (Doku) | Verhalten (C03, Session-only) |
| D | eigener Audit-Kanal + Format-Tests | Event-Modell, Replay |

Querschnitt: P0-2-Entscheidung ist unabhängig von P0-1 (getrennte Optionen je P0, G7-01: „Watchdog-Fix als P0-1-Erledigung verbuchen" ❌ verboten [F(ARB_IMPLEMENTATION_CONTRACTS RC-1b)]); ohne Entscheidung bleiben wiederholte Alarme und fehlende Historie [F(RC1-Brief §7)].

---

## 3. RC-2 — HDR-001

### 3.1 Verhältnis der Options-Ebenen

| Ebene | Optionsraum | Entscheider |
|-------|-------------|-------------|
| Governance-Form (HDR-001): Annehmen ohne/mit Auflagen / Ablehnen / Teilfreigabe | A/B/C/D (HDR-001_DECISION_RECORD §3) | ARB/Human [F] |
| Architektur-Form (Simulation, Aufgabe): wie der Cognitive-OS-Pfad gebaut wird | A MUSCAL CORE evolutionär · B Hybrid CORE + muscal/ · C Neubau Cognitive OS Layer | ARB/Human — **kein Agenten-Mandat** [F(HDR-001 §5: „Dieser Agent: KEINE Entscheidungsbefugnis")] |

Beobachtung: Die Architektur-Form ist eine Folge-Frage der Annahme („mit welchen Auflagen?"); sie steht nicht im HDR-001-Text und muss vom Entscheider als separate Dimension deklariert werden [I]. Die hier simulierten Optionen A/B/C sind **Simulations-Frames, keine neuen Registry-Einträge** [I].

### 3.2 Faktenlage

| # | Aussage | Marke |
|---|---------|-------|
| F20 | HDR-001: Architecture Council (Gesamt-Governance); HDR-002 PMGA, HDR-003 Master Coding AI, HDR-004 Requirements Engineering — HDR-002…004 blockiert (9 Dependencies) | [F(HDR-001_DECISION_RECORD §1)] |
| F21 | READY FOR HUMAN DECISION seit 20.07; D-023 unresolved; M2-Eingangsgröße HDR-001-Status | [F(PROJECT_STATE:116-119; 05_DECISION_REGISTRY §B)] |
| F22 | Reife-Indikatoren: MC-TC-004 CERTIFIED WITH CONDITIONS; MC-TC-007 CONDITIONAL GO; Readiness 74.8 | [F(HDR-001_DECISION_RECORD §2)] |
| F23 | kein Code-Impact der HDR-001-Entscheidung (Gremium, kein Modul) | [F(KF5 §4.1)] |
| F24 | ADR-001 APPLIED (Single Pipeline Authority); D-010 (MUSCAL 2.0 Hybrid, chat-only, C2) mit Migrationspfad undefiniert (MEDIUM) | [F(ADR-001; 05_DECISION_REGISTRY §D)] |
| F25 | `muscal/` existiert als eigenständiges Python-Paket (pyproject.toml, src/, tests/, README: „AI Verification Runtime" mit Claim→Runtime→Reality-Pipeline) — separates Projekt im Workspace | [F(Code/README)] |
| F26 | MUSCAL-2.0-Turnier-Sieger: Hybrid (durable execution + hierarchisches Multi-Agenten-Modell + event-driven verification); nur Chat, kein Repo-Beleg | [F(ADR-022 §Context)] |
| F27 | ADR-023 (Cognitive Kernel: Intent/Goal/Context/Strategy-Engines), ADR-024 (Agent-Architektur), ADR-025 (Cognitive Compiler) — alle DRAFT, nicht akzeptiert | [F(ADR-INDEX)] |

### 3.3 Simulations-Optionen und Bewertung

#### Option A — MUSCAL CORE evolutionär

| Dimension | Bewertung | Marke |
|-----------|-----------|-------|
| Architektur | Fortsetzung des D-001-Pfads (ADR-001 APPLIED); Cognitive-OS-Elemente als features/-Plugins (Kernel-Audit: Intent/Goal/Context-Engines wären feature-seitig zu bauen) | [I] |
| Migration | keine — keine Architektur-Formänderung; D-010 bleibt CHAT_ONLY/unverbindlich | [F] |
| Testaufwand | niedrig: Governance-Doku + ggf. Plugin-Tests; kein Umbau | [I] |
| Risiko | niedrig: kein bestehender Pfad wird verlassen; aber MUSCAL-2.0-Direction wird nicht vorbereitet (Turnier-Sieger D-010 bleibt ungenutzt) | [I] |
| MUSCAL-2.0 | widerspricht nicht, unterstützt aber nicht: Hybrid-Migration bliebe vollständig späterer Arbeit (Migrationspfad ohnehin undefiniert) | [I] |
| Agent Architecture | HDR-002…004 starten im Single-Agent-Kernel-Rahmen; Master Coding AI (HDR-003) könnte Core-Änderungen fordern → Override-Pfad (D-020) | [I] |
| Wartbarkeit | höchste Stabilität (kein Zweistrang); aber Cognitive-OS-Ambition (ADR-023-Konzept) bleibt aufgeschoben | [I] |

#### Option B — Hybrid CORE + muscal/

| Dimension | Bewertung | Marke |
|-----------|-----------|-------|
| Architektur | zweigleisig: MUSCAL CORE (Single-Agent-Pipeline) + `muscal/`-Paket (Verification-Runtime mit Claim→Reality-Muster, F25) parallel; Integrationsfrage: wer orchestriert? (Schnittstellen-Vertrag fehlt) | [I] |
| Migration | hoch: Zwei-Projekt-Betrieb (zwei pyproject-Bäume, zwei Test-Welten); Zuständigkeitsüberlappung Kernel↔Verification-Runtime | [I] |
| Testaufwand | hoch: beide Suiten getrennt; Integrations-/Kontrakttests zwischen CORE und muscal/ neu | [I] |
| Risiko | mittel–hoch: Duplikation von Governance/Persistenz-Fragen; D-010-Konflikt (MEDIUM) wird nicht gelöst, sondern kopiert | [I] |
| MUSCAL-2.0 | kompatibel mit Turnier-Hybridrichtung (durable execution existiert in beiden: EventStore vs. Verification-Runtime) — aber ohne ADR-022-Migrationsbewertung unverbindlich | [I] |
| Agent Architecture | HDR-002…004 starten im CORE-Rahmen; muscal/-Eigenschaften (Verifikation als Runtime-Prinzip) wären Integrationsthemen für HDR-003 | [I] |
| Wartbarkeit | teuer: zwei Wahrheitssysteme (CORE-Doku vs. muscal/-Runtime) erfordern permanente Abstimmung | [I] |

#### Option C — Neubau Cognitive OS Layer

| Dimension | Bewertung | Marke |
|-----------|-----------|-------|
| Architektur | neuer Layer gemäß ADR-023-Muster (Intent→Goals→Context→Strategy→Planner→Runtime) [F(COGNITIVE_KERNEL_AUDIT §3)]; Design-Frage: Core-Status des Layers (D-020) vs. features/-Plugin (D-006) | [I] |
| Migration | größte: alle Bestandsmodule müssten als Konsumenten des Layers bewertet werden; ADR-001-Pipeline-Autorität (F24) wäre berührt | [I] |
| Testaufwand | höchster: neue Engine-Suiten (Intent/Goal/Context/Strategy), Konsistenz zu bestehenden Pfaden; Baseline-Erweiterung | [I] |
| Risiko | hoch: abhängig von RC-4a (ADR-022…025 sind DRAFT — Design-Rahmen nicht akzeptiert, F27); P0-1/P0-2 blieben davon unberührt offen | [I] |
| MUSCAL-2.0 | volle Ausrichtung auf Turnier-Sieger; aber Migrationspfad D-010↔D-001 undefiniert (MEDIUM) — Richtungsbindung nicht belastbar | [I] |
| Agent Architecture | entspricht ADR-024/023-Ambition (hierarchisches Multi-Agenten-Modell); HDR-Rollen bekämen klaren Layer-Bezug | [I] |
| Wartbarkeit | mittelfristig sauber (expliziter Layer), kurzfristig teuer (Parallelinfrastruktur bis Ablösung) | [I] |

### 3.4 Entscheidungsfolgen (RC-2)

| Aspekt | Option A (evolutionär) | Option B (Hybrid) | Option C (Neubau) |
|--------|------------------------|-------------------|-------------------|
| HDR-Entblockung | unabhängig möglich (Annahme-Form A/B/D entscheidet) | unabhängig; aber Arbeitsplanung der HDRs hängt an Zweistrang-Integration | unabhängig; HDR-003-Startrampen bräuchten Layer-Design |
| M2-Eingangsgröße | HDR-001-Status (nicht Architektur-Form) entscheidet M2-Wirkung [F18…F21] | wie A | wie A |
| RC-6-Messgate | M4-K3/M2 nur via Re-Messung — Formänderung allein ändert keine Scores | wie A | wie A |
| P0-1/P0-2 | unabhängig offen (G7-01) — keine Option berührt die P0-Entscheidungen | wie A | wie A |
| MUSCAL-2.0 | ohne Wirkung | vorbereitend | vorbereitend, aber abhängig von RC-4a |

Gemeinsam: Alle drei Formen ändern **keine** der offenen P0-/Messgate-Status (formale Messung nur bei Re-Messung, 18_METRIC_REGISTRY §6-1) [F].

---

## 4. Cross-Cutting — Interaktionsfolgen

| Kombination | Folge | Marke |
|-------------|-------|-------|
| RC-1a A/C + RC-1b A/B | beide berühren die EventStore/Replay-Zone (Impact-Graph §6: Risikokonzentration) → Sequenzierung/Doppelpersistenz-Prüfung wird zwingend | [I] |
| RC-1a B (Dual Truth) + RC-1b B | Dual-Truth-Konsistenz trifft auf deduplizierte Watchdog-Events → Konflikt-Urteil nötig (welche Wahrheit für wiederholte Orphans) | [I] |
| RC-2 C (Neubau) + RC-1a/R C-1b | P0-Lösungen entstehen im alten Kernel, während der Cognitive-OS-Layer neu gebaut wird → Doppelarbeit-Risiko für Graph-/Watchdog-Pfade | [I] |
| RC-2 B (Hybrid) + RC-4a (ADR-022…025) | Hybrid-Richtung hängt an der ADR-022-Migrationsbewertung (NOT READY) — Reihenfolge: Review vor Richtungsbindung | [I] |
| Jede Wahl + RC-6 | Mess-Gate bleibt abhängige Größe: Entscheidungen notwendig, nicht hinreichend (KF3-H-1) | [F] |
| Jede Wahl + Freeze-Policy | FREEZE_POLICY_UPDATE §2-Freeze-Zonen: Event-Modell, ADR-State, Baselines bleiben bis ARB unverändert; Aufhebung nur durch Entscheider (R-5) | [F] |

## 5. Simulation-Grenzen

1. Keine Empfehlung, keine GO/NO-GO, keine Priorisierung durch den Agenten [F(G7-01)].
2. [H] sind als ungeprüfte Annahmen zu verstehen; jede Hypothese, die in eine Entscheidung einfließt, ist vor dem ARB zu verifizieren.
3. Aufwands-/Risiko-Aussagen ohne Quellen-Skala sind Modell-Ableitungen ([I]), keine Messungen.
4. Die Simulations-Szenarien (RC-1a A/B/C, RC-2 A/B/C) erweitern den G7-01-/HDR-001-Optionsraum nicht; jede umsetzungsrelevante Wahl muss als bestehende Option deklariert werden [I].
5. ADR-022/023/024/025 bleiben DRAFT; keine Akzeptanzannahme (G4.5-B2) [F].

## Validation

- Read-only: keine Implementierung, keine ADR-Erstellung, keine Codeänderung, keine Statusänderung, keine Score-Berechnung; alle [F] mit Quelle (Datei:Zeile oder Artefakt); [I]/[H] klar getrennt.
- Konsistent mit ARB_IMPLEMENTATION_CONTRACTS (Decision/Agent/Validation Boundaries, Forbidden Actions), KF5_IMPLEMENTATION_READINESS_MAP (§7-Szenarien), IMPLEMENTATION_SEQUENCE_ANALYSIS, RC6_GATE_PREPARATION_MATRIX und FREEZE_POLICY_UPDATE.
- Statuslage unverändert: RC-1 PENDING HUMAN, RC-2 HUMAN REQUIRED, RC-4a NICHT GESTARTET, RC-6 ausstehend.
