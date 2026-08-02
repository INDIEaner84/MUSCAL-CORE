# RC-6 ARCHITECTURE DECISION READINESS REPORT

- Datum: 02.08.2026
- Phase: RC-6 Decision Closure — Preparation (read-only)
- Verfasser-Rolle: MUSCAL Architecture Steward (Principal Software Architect / Distributed Systems Reviewer / Verification Architecture Auditor / ADR Reviewer)
- Mandat: Analyse, Evidenz-Trennung, Entscheidungsraum-Vorbereitung, Risiko-Sichtbarmachung, Implementierungsfolgen-Bewertung — **keine Empfehlung, keine Entscheidung, keine Dateiänderung, kein Commit, keine Migration**
- Arbeitsregel geprüft: Existiert eine ARB/Human-Freigabe für Änderungen? → **Nein** → Nur Analyse. ✅ eingehalten
- Status: **created, not committed (external KF layer)**

---

## KENNZEICHNUNG

| Marke | Bedeutung |
|-------|-----------|
| **FACT** | Direkt im Repository nachweisbar (Datei:Zeile / Artefakt) |
| **INFERENCE** | Logische Schlussfolgerung aus Fakten |
| **HYPOTHESIS** | Mögliche zukünftige Interpretation |
| **SPECULATION** | Nicht ausreichend belegte Möglichkeit |

---

# Status

- Datum: 2026-08-02
- Phase: RC-6 Decision Closure — **CONDITIONAL GO** (MC-TC-007, 31.07) mit 2 P0-Blockern offen
- Repository-Status: P0-1 OFFEN, P0-2 OFFEN, HDR-001 READY FOR HUMAN DECISION, ADR-022…025 DRAFT
- Steward-Handlung: ausschließlich Analyse (kein Schreibzugriff auf MUSCAL CORE)

---

# Evidenz

## E1. Systemlandschaft (FACT)

| # | Aussage | Beleg |
|---|---------|-------|
| E1.1 | MUSCAL CORE = produktive Pipeline Runtime mit kernel.py, EventBus, GraphState, Memory, RAG, Plugin-System (features/) | PROJECT_STATE.md; Repo-Struktur |
| E1.2 | muscal/ = eigenständiges Python-Paket „AI Verification Runtime" mit CLAIM→Runtime→Reality-Pipeline; Module: claims, evidence, reality, verification, security, governance, cognitive_os, prompt_compiler, workflow, simulation, compliance, incidents, tenant, mreil | muscal/README.md; muscal/src/muscal/ (Verzeichnisinventar) |
| E1.3 | Beide Systeme sind verschiedene Architekturphilosophien: CORE = pragmatische Execution Runtime; muscal/ = formale Trust/Verification Architecture | README-Formulierung „MUSCAL is not an agent library. MUSCAL is an AI Verification Runtime" (FACT); Philosophie-Differenz als INFERENCE aus E1.1/E1.2 |
| E1.4 | EventStore: SQLite-append-log; Docstring „This is the SINGLE CANONICAL EVENT AUTHORITY for all production events" | runtime/event_store.py:37 |
| E1.5 | EventStore-Schema: seq (AUTOINCREMENT), topic, payload, source, priority, timestamp, event_id UNIQUE, execution_id, correlation_id, causation_id, execution_mode, execution_state, verification_state, is_replayed, receipt_id, schema_version | runtime/event_store.py:50-67 |
| E1.6 | EventStore.append() unterdrückt Replay-Marker (`_replayed` → None) — Schutz gegen Replay-Schleifen | runtime/event_store.py:93-95, 112-119 |
| E1.7 | EventStore.append() erzwingt execution_id für _EXECUTION_REQUIRED_TOPICS; EXECUTION_FAILED gehört NICHT zu diesen Topics | runtime/event_store.py:21-32, 97-101 |
| E1.8 | „verified" ist im Store evidenzpflichtig: ohne receipt_id+execution_id wirft store_verification() EvidenceRequiredError; Konflikt verified/failed wirft VerificationConflictError | runtime/event_store.py:202-231 |
| E1.9 | GraphState: in-memory nodes dict + edges list; _update_stream; _replaying-Flag existiert bereits | graph.py:48-57, 226-229 |
| E1.10 | Graph-Events: NODE_CREATED (node_id, type, payload, timestamp, execution_id); NODE_UPDATED (**ohne payload-Feld**); EDGE_CREATED (source_id, target_id, edge_type — ohne payload, ohne timestamp) | graph.py:77-83, 103-108, 124-128 |
| E1.11 | node_id = f"{node_type.lower()}_{counter}" — deterministisch aus _node_counter | graph.py:66 |
| E1.12 | Pruning (MAX_NODES 5000 / MAX_EDGES 10000) entfernt älteste Knoten/Kanten **ohne Events zu erzeugen** | graph.py:41-42, 145-158 |
| E1.13 | remove_node/remove_edge erzeugen keine Events | graph.py:133-143 |
| E1.14 | ExecutionWatchdog besitzt event_store-Referenz und **liest** bereits: get_cursor() + replay(cursor=0, limit=5000) für Orphan-Scan | features/monitoring/execution_watchdog.py:60-76 |
| E1.15 | _force_fail_orphan() ruft NUR event_bus.publish("EXECUTION_FAILED", …) mit verification_state="unverified" — kein EventStore.append | execution_watchdog.py:96-119 |
| E1.16 | Watchdog hat Core-Import `from event_bus import EventPriority` | execution_watchdog.py:97 |
| E1.17 | EventStoreAdapter (features/events/event_adapter.py:75-85) ist der vorhandene Rückkanal: append_writer_event → writer_to_eventstore → EventStore.append; id = idempotency_key oder md5(type_ts_actor) | event_adapter.py:8-26, 69-72, 75-85 |
| E1.18 | EventStore.append() ist idempotent-fähig: event_id UNIQUE → doppelter append wirft sqlite3.IntegrityError | runtime/event_store.py:57, 80-86 |
| E1.19 | MC-TC-004 CERTIFIED (33/33, 431/431 Tests); MC-TC-006 (Replay deterministisch) CERTIFIED; MC-TC-005 NOT AUTHORIZED; MC-TC-007 CONDITIONAL GO | PROJECT_STATE.md:18-24 |
| E1.20 | Baseline 470 (D-041); FL-01a (19 flaky Tests, globale Singletons) dokumentiert nicht gefixt; FL-01b kalibriert | DECISION_REGISTRY D-040/D-041; PROJECT_STATE.md:128-129 |
| E1.21 | D-006 (features/-Pflicht), D-020 (Core immutable, OVERRIDE + --allow-core-write), D-008 (EventBus/EventStore/AuditLog nicht verschmelzen), D-009 (append-Signatur prüfen) | DECISION_REGISTRY §A/§B; SESSION_RULES v2.0 |
| E1.22 | P0-1 (Graph-OS nicht rekonstruierbar) = PA-08, Restart-Risiko R1 HIGH; P0-2 (Watchdog nicht persistent) = PA-09, Folge-Finding C03 (Doppelalarme) | PROJECT_STATE.md:43-48; 16_BLOCKER_REGISTRY; G7-01 |
| E1.23 | HDR-001 READY FOR HUMAN DECISION seit 20.07; blockiert HDR-002…004 (9 Dependencies); D-023 unresolved; M2-Eingangsgröße | PROJECT_STATE.md:112-119; DECISION_REGISTRY D-023 |
| E1.24 | ADR-022…025 DRAFT/PROPOSED; keine Akzeptanz; Migrationspfad D-010↔D-001 undefiniert (MEDIUM) | spec/ADR-022…025; DECISION_REGISTRY §D |
| E1.25 | SOURCE_OF_TRUTH: TECHNICAL_BASELINE/ARCHITECTURE stale (12.07); neueste Wahrheit liegt in docs/audit/ (untracked) + Chat | SOURCE_OF_TRUTH_MAP.md FINDING A1/A2 |
| E1.26 | muscal/ besitzt Module für Temporal Concepts/Truth Model/Governance: governance/, reality/, verification/, claims/, security/, simulation/ | muscal/src/muscal/ (Verzeichnisinventar) |

---

# Architekturinterpretation

## I1. Gesamtsystem (INFERENCE)

- I1.1: CORE und muscal/ sind komplementäre Layer-Kandidaten: CORE liefert Event-Persistenz (EventStore) und Execution; muscal/ liefert formale Verifikations-Semantik (Claims, Evidence, Reality) — eine Kopplung ist heute nicht implementiert (kein Import/Integrationscode zwischen beiden).
- I1.2: Der EventStore ist der einzige Kandidat für eine langfristige Truth Layer, weil er append-only, sequenziell (seq), versioniert (schema_version), audit-fähig (source/priority/timestamp) und zertifiziert (MC-TC-004) ist — aber NICHT, weil er heute schon als Truth Layer genutzt wird: GraphState und Watchdog-Wahrheiten laufen an ihm vorbei.
- I1.3: EventBus ist Transport (Distribution), keine Audit-Wahrheit — bestätigt durch D-008 (Trennung) und den fehlenden append im Watchdog (E1.15). (Prinzip 3 der Aufgabe: bestätigt)

## I2. RC-1a — Event Truth Model (INFERENCE/HYPOTHESIS)

### Option A — EventStore als Single Truth

- I2-A1: Rebuild aus stored_events ist **prinzipiell deterministisch möglich**: node_id-Vergabe über Counter (E1.11) und Replay-Reihenfolge (seq ASC, event_store.py:328) sind reproduzierbar; `_replaying`-Flag existiert bereits (E1.10).
- I2-A2: **Vollständigkeits-Lücken im Event-Log (FACT)** schränken die Rekonstruktions-Treue ein: (a) NODE_UPDATED transportiert kein payload-Delta (E1.10) → Payload-Updates gehen verloren; (b) Pruning und remove_node/remove_edge erzeugen keine Events (E1.12/E1.13) → Rebuild ohne identische Pruning-Logik wächst über MAX_NODES/MAX_EDGES; (c) EDGE_CREATED ohne payload/timestamp (E1.10).
- I2-A3 (INFERENCE): Rebuild = Replay + deterministische Wiedergabe von (1) add_node/update_node/add_edge-Aufrufen in seq-Reihenfolge und (2) Pruning-Strategie; Abweichungen wären nur bei payload-Update-Verlust und fehlenden Lösch-Events (I2-A2).
- I2-A4 (HYPOTHESIS): Bei Pruning als deterministischer Rebuild-Regel (älterer Knoten fliegt raus, sobald 5000 überschritten) konvergieren Rebuild-Ergebnis und „Live"-Graph gegen denselben Zustand — Testbar über Rebuild-Tests (Rekonstruktion ≡ Event-Log).
- I2-A5 (INFERENCE): Single Truth macht den in-memory GraphState zur Projektion; jede Schreibseite (nur public API) ist gleichzeitig Event-Quelle — D-008 bleibt gewahrt (EventBus unberührt).

### Option B — Dual Truth EventStore + GraphState

- I2-B1 (INFERENCE): Dual Truth = in-memory GraphState primär (heutiger Zustand) + EventStore parallel → zwei Autoren mit Konsistenzpflicht; Drift-Zustände sind die Folge, wenn Ereignisse fehlen (I2-A2) oder die Reihenfolge der beiden Wahrheiten divergiert.
- I2-B2 (HYPOTHESIS): Drift kann nur über periodischen Vergleich (Snapshot vs. Rebuild) erkannt, nicht verhindert werden — ein „Reconciliation-Report" würde zur neuen Pflichtkomponente.
- I2-B3 (INFERENCE): Konsistenz-Semantik (welche Wahrheit gewinnt bei Konflikt?) ist eine Entscheidung, die der G7-01-Optionsraum A/B/C/D nicht abbildet → Dual Truth ist heute kein deklarierbarer Optionsraum (deckungsgleich mit ARB_DECISION_SIMULATION-Ergebnis).

### Option C — EventStore + Reconstruction Layer

- I2-C1 (INFERENCE): Reconstruction Layer = explizite Schicht zwischen EventStore und GraphState (Replay → Rebuild → GraphState-API); übernimmt die Funktion von I2-A3 als eigenständige, testbare Komponente in features/ (D-006).
- I2-C2 (INFERENCE): Abgrenzungspflicht gegen ReplayService (MC-TC-006-deterministisch): Replay liefert Events, Reconstruction konsumiert sie — Überlappung nur, wenn ReplayService selbst Rebuild-Funktionen bekommen soll.
- I2-C3 (HYPOTHESIS): Die Schicht ist als MUSCAL-2.0-Modul (durable execution) wiederwendbar; der Layer-Kontrakt (Event→GraphState-Operationen) würde zur stabilen Schnittstelle.

## I3. RC-1b — Watchdog Persistence (INFERENCE/HYPOTHESIS)

- I3-1 (FACT→INFERENCE): „Watchdog → EventStore → EventBus" bedeutet konkret: `_force_fail_orphan()` appendet EXECUTION_FAILED via EventStoreAdapter (E1.17) UND publiziert weiter via EventBus (E1.15) — EventBus-Rolle bleibt (Distribution), EventStore wird zur persistierten Wahrheit.
- I3-2 (INFERENCE): Dedup (C03) ist im EventStore-Schema bereits **nativ verfügbar**: event_id UNIQUE (E1.18). Ein deterministischer idempotency_key (z. B. f"orphan_{execution_id}") würde Doppelappends per IntegrityError abfangen — Dedup ohne neuen Marker-Code.
- I3-3 (INFERENCE): verification_state="unverified" (E1.15) passt zur Store-Semantik (Default unverified, E1.5); eine spätere Verifikation des Orphan-Befunds wäre über store_verification() mit receipt-Pflicht möglich — CLAIM != PROOF (Prinzip 4) ist im Store implementierbar, nicht nur im Chat.
- I3-4 (INFERENCE): EXECUTION_FAILED ist kein _EXECUTION_REQUIRED_TOPIC (E1.7) → append ohne execution_id wäre möglich, aber Watchdog hat die execution_id ohnehin (payload) — kein Migrationsthema.
- I3-5 (HYPOTHESIS): Da der Watchdog bereits replay()-basiert scannt (E1.14), ist der Umstieg auf append + Dedup für denselben Scan-Durchlauf ohne neuen Scan-Mechanismus nutzbar (persistente Erkennungen statt Neu-Erkennung nach Restart).

## I4. HDR-001 — Ebenen-Trennung (INFERENCE)

- I4-1: Governance-Entscheidung (Annahme-Form A–D: ohne/mit Auflagen, Ablehnung, Teilfreigabe) und Architekturentscheidung (1 evolutionär / 2 Hybrid / 3 Neubau Cognitive OS) sind orthogonal: Auch bei Annahme mit Auflagen (Governance B) bleibt die Architekturform offen; auch ohne Annahme kann die Architekturrichtung vorbereitet (nicht umgesetzt) werden.
- I4-2 (INFERENCE): Vermischung wäre dann gegeben, wenn eine HDR-001-Antwort die Architekturform impliziert (z. B. „annehmen" = „MUSCAL CORE evolutionär") — das ist weder im Decision Record noch in D-023 deklariert.
- I4-3 (INFERENCE): Die Architekturform (1/2/3) hat heute **keinen Code-Impact**, weil HDR-001 ein Gremium ist (kein Modul) — jede Form-Aussage ist eine Richtungsdeklaration, keine Umsetzung (deckungsgleich mit KF5 §4.1).

---

# Risiken

| ID | Risiko | Ebene | Status | Quelle |
|----|--------|-------|--------|--------|
| R1 | Restart verliert Graph-Zustand (P0-1) — Anwendungsfälle mit persistenter Session unwirksam; Verifikations-Graph geht verloren | HIGH | OFFEN | G5 R1; 16_BLOCKER_REGISTRY PA-08 |
| R2 | Payload-Updates und Pruning/Löschungen sind im Event-Log nicht repräsentiert — Rebuild wäre ohne Gegenmaßnahmen unvollständig (I2-A2) | HIGH (für Option A/C) | NEU (Code-Befund) | graph.py:103-108, 133-158 |
| R3 | Watchdog-Erkennungen überleben Restart nicht; Doppelalarme (C03) | MEDIUM-HIGH | OFFEN | G7-01; PA-09 |
| R4 | Doppelpersistenz: neuer Watchdog-append könnte Replay-Determinismus (MC-TC-006) brechen, wenn die Replay-Matrix nicht geprüft wird | MEDIUM | Voraussetzung | G7-01; MC-TC-006 |
| R5 | Dual-Truth-Drift (Option B) ohne Reconciliation-Pflichtkomponente | MEDIUM | Konzeptionell | I2-B2 |
| R6 | HDR-Deadlock (R2) hält an; HDR-002…004 blockiert; v0.8-Manual-Autorität ungeregelt | HIGH | OFFEN | G5 R2 |
| R7 | ADR-022…025 DRAFT: jede Architekturform-Aussage (HDR-001-Form 2/3) bindet Richtung ohne akzeptierten Rahmen | MEDIUM-HOCH | OFFEN | ADR-INDEX |
| R8 | CHAT_ONLY-Wissen (MUSCAL 2.0, Audit-Status) ist für frische Sessions unsichtbar — Fehl-Entscheidungen auf veralteter Basis | HIGH | OFFEN (dokumentiert) | SOURCE_OF_TRUTH_MAP A2; MASTER_INDEX TF-03 |
| R9 | Test-Flakiness (FL-01a, globale Singletons) kann neue Rebuild-/Watchdog-Tests verfälschen (Fixture-Fläche) | MEDIUM | OFFEN | D-040 |
| R10 | Freeze-Widerspruch („ALL P0 BLOCKERS RESOLVED" vs. Reality) bleibt unaufgelöst und erzeugt Wahrheits-Ambiguität für ARB | MEDIUM | OFFEN | GRAPH_OS_ARCHITECTURE_FREEZE_v1.0 |

---

# Offene Entscheidungen

| ID | Entscheidung | Optionen | Status | Entscheider |
|----|--------------|----------|--------|-------------|
| D-01 | RC-1a Event Truth Model: Single Truth / Dual Truth / Reconstruction Layer | A / B / C | PENDING HUMAN (P0-1) | ARB/Human |
| D-02 | RC-1b Watchdog Persistenz: append-Pfad + Dedup-Strategie | A / B / C / D (G7-01) | PENDING HUMAN (P0-2) | ARB/Human |
| D-03 | HDR-001 Governance-Form | A / B / C / D | READY FOR HUMAN DECISION (20.07) | ARB/Human |
| D-04 | HDR-001 Architekturform (getrennt von D-03!) | 1 evolutionär / 2 Hybrid / 3 Neubau | **nicht deklariert** — als eigene Frage zu stellen | ARB/Human |
| D-05 | ADR-022…025 Status | PROPOSED-final / DEPRECATED / ACCEPTED | NICHT GESTARTET (RC-4a) | ARB/Human |
| D-06 | MC-TC-005 Autorisierung | AUTHORIZED / weiter NOT AUTHORIZED | NOT AUTHORIZED | ARB/Human |
| D-07 | Dual-Truth-Abweichung (falls RC-1a=B) | Konsistenz-Semantik definieren | Konzeptionell offen | ARB/Human |
| D-08 | Rebuild-Vollständigkeit (falls RC-1a=A/C) | payload-Delta + Lösch-/Prune-Events in Rebuild-Regel behandeln | Technische Klärung (Agent nach Freigabe) | Agent (nach Entscheidung) |

---

# Auswirkungen

## Wenn RC-1a = Option A (EventStore Single Truth)

- Architekturfolgen: GraphState wird Projektion; Rebuild-Service in features/ (D-006); Boot-Phase-K-Integration; `_replaying`-Flag wird genutzt (existiert); **keine Core-Änderung** (nur public API).
- Migration: kein Bestands-Code zu ändern; neue Komponente + Boot-Wiring; Aufwand M–L (DECISION_CLOSURE_PACKAGE §RC-1).
- Risiko: R2 (Log-Lücken) wird wirksam — Rebuild-Treue hängt an payload-Delta/Lösch-Events; R4 (Replay) prüfen.
- Testaufwand: hoch — Rebuild-Tests (Rekonstruktion ≡ Log, Counter-Reihenfolge, Pruning), Boot-Integration, Baseline-Erweiterung (kalibriert, D-041), FL-01a-Fläche wächst.
- MUSCAL-2.0: kompatibel mit „durable execution" (Turnier-Sieger); Layer-Kontrakt als Basis nutzbar.
- Agent Architecture: Agenten-Sessions bekommen wiederherstellbaren Graph (Identity/Provenance-Grundlage); muscal/-Verifikations-Semantik (claims/evidence) bleibt unberührt.
- Wartbarkeit: eine Wahrheitsquelle; Rebuild-Tests wachsen — kontrolliert.

## Wenn RC-1a = Option B (Dual Truth)

- Architekturfolgen: zwei Autoren (GraphState primär + EventStore parallel); Konsistenz-/Reconciliation-Pflicht entsteht.
- Migration: kein Bestandsumbau; Konsistenz-Semantik (D-07) neu.
- Risiko: R5 (Drift) — ohne Reconciliation permanent unsichtbare Abweichungen; R1 nur teilweise adressiert (Recovery = letzter konsistenter Stand).
- Testaufwand: höchster — Vergleichs-/Drift-Tests mit neuem Orakel.
- MUSCAL-2.0: konfliktär zur durable-Execution-Einheitsquelle (I2-B).
- Agent Architecture: Agenten können je nach Leseweg unterschiedliche Wahrheiten sehen.
- Wartbarkeit: teuerste Variante (Doppel-Buchführung).

## Wenn RC-1a = Option C (EventStore + Reconstruction Layer)

- Wie Option A, plus expliziter Layer-Kontrakt; zusätzliche Abgrenzung gegen ReplayService (I2-C2).
- Testaufwand: wie A plus Schnittstellen-Kontrakttests.
- MUSCAL-2.0: Layer als wiederverwendbares Modul (I2-C3) — beste Migrations-Fluidität.
- Agent Architecture/Wartbarkeit: wie A.

## Wenn RC-1b = Watchdog → EventStore → EventBus

- EventStore-Integration: append via EventStoreAdapter (E1.17); ein Feature-File betroffen; Dedup über idempotency_key + UNIQUE (I3-2) — C03 adressierbar ohne neuen Marker.
- EventBus-Rolle: unverändert Distribution (D-008 bleibt); kein Verschieben von Verantwortung.
- Auditfähigkeit: Fehler-Historie überlebt Restart; Orphan-Befunde mit verification_state=unverified als Claims im Log (CL AIM != PROOF-Fundament vorhanden, E1.8).
- Replayfähigkeit: neue EXECUTION_FAILED-Events laufen durch deterministisches Replay; MC-TC-006-Matrix-Prüfung ist Voraussetzung (R4).
- Fehlermodell: Erst-/Wiederholungserkennung wird unterscheidbar; Dedup verhindert Doppelalarme.
- Persistenzkosten: minimal (1 Insert je Orphan-Erkennung; SQLite-Bound); Baseline-Erweiterung; kein Speicher-Engpass absehbar (HYPOTHESIS).
- Core-Kopplung: unverändert — `from event_bus import EventPriority` (E1.16) bleibt; kein neuer Core-Import nötig; Append über Feature-Adapter (kein Core-Write).
- Aufwand: S (Option A) / S–M (Option B inkl. Dedup) (DECISION_CLOSURE_PACKAGE §RC-1).

## Wenn HDR-001 Governance (D-03) + Architekturform (D-04)

- Governance A/B: HDR-002…004 entblockt; M2-Rest adressierbar; v0.8-Manual-Autorität regelbar — mit Evidence-Pflicht (B) oder ohne Review-Hürde (A).
- Governance C: Deadlock hält; M2-Rest bleibt; Arbeitsplanung HDR-003 (Master Coding AI) auf unsicherer Basis.
- Architekturform 1 (evolutionär): CORE bleibt D-001-Pfad; D-010 (MUSCAL 2.0) bleibt CHAT_ONLY; niedrigstes Risiko, keine Richtungsbindung.
- Architekturform 2 (Hybrid CORE + muscal/): Zwei-Projekt-Betrieb (eigene pyproject-Bäume); Integrationsvertrag fehlt; Kompatibilität mit ADR-001-Pipeline-Autorität ungeklärt (R7).
- Architekturform 3 (Neubau Cognitive OS): deckungsgleich mit ADR-023-Muster (Intent→Goals→Context→Strategy→Planner→Runtime); größte Migration; abhängig von RC-4a (D-05).
- Unabhängig von D-03/D-04: P0-1/P0-2 bleiben offen (G7-01: getrennte Entscheidungen); keine Score-Wirkung ohne formale Re-Messung.

---

# Empfehlung

**Keine Empfehlung** — nicht angefordert und durch Mandat ausgeschlossen (keine Empfehlung ohne menschliche Freigabe). Die vorstehenden Auswirkungen sind Entscheidungsfolgen, keine Präferenzen.

---

# Validation

- Read-only eingehalten: keine Datei im MUSCAL CORE verändert, kein Commit, keine Migration, keine ADR-Erstellung.
- Alle FACT mit Datei:Zeile-Beleg; INFERENCE als Schlussfolgerung gekennzeichnet; HYPOTHESIS/SPECULATION nicht als Fakten formuliert.
- Kein Score berechnet, kein GO/NO-GO ausgesprochen, keine Empfehlung gegeben.
- Konsistent mit KF-3/KF-4/KF-5/KF-6-Artefakten und ARB_DECISION_SIMULATION_REPORT.md; neue Code-Befunde (R2, I3-2, E1.10/E1.12/E1.14) erweitern die Evidenzbasis ohne Statusänderung.
