# COGNITIVE_LEDGER_ARCHITECTURE_REVIEW

Prüfung: Kann MUSCAL EventStore v2 als Cognitive Ledger dienen?

- Datum: 02.08.2026
- Modus: **READ ONLY** — nur Analyse, keine Codeänderung, kein Commit, keine automatische Entscheidung, keine Empfehlung als Fakt
- Kennzeichnung: [F] FACT (Datei:Zeile) · [I] INFERENCE · [H] HYPOTHESIS
- Quellen: EVENT_SOURCING_INTEGRITY_ANALYSIS.md [ESIA], STATE_TRANSITION_EVENT_ANALYSIS.md [STE], B2_HYBRID_ARCHITECTURE_DECISION_PACKAGE.md [B2PKG], B2_HYBRID_MIGRATION_ANALYSIS.md [B2MA], ARB_DECISION_SIMULATION_REPORT.md [SIM], SESSION_RULES v2.0 [SR], DECISION_REGISTRY.md [REG], PROJECT_STATE.md [PST], muscal/-README [MR], Code-Stand 02.08.2026
- Status: **created, not committed (external KF layer)**

---

## 1. Unterschied: Execution Event Log vs Cognitive Ledger

### 1.1 Execution Event Log (heutige Funktion)

- [F] Zweck: append-only Persistenz von Produktions-Events mit Cursor-Replay, „SINGLE CANONICAL EVENT AUTHORITY" [F: runtime/event_store.py:36-37]; Replay für Verarbeitung/Wiederherstellung [F: runtime/event_store.py:305-332; features/replay/replay_service.py:22-82].
- [F] Fokus: **Ablauf** (was passierte in welcher Reihenfolge): seq, topic, payload, timestamp, execution_id, correlation_id, causation_id, execution_mode, execution_state, verification_state [F: runtime/event_store.py:50-67].
- [I] Kern-Frage des Logs: „Welches Ereignis geschah wann und in welcher Ausführungs-Kette?" [I]

### 1.2 Cognitive Ledger (Ziel-Rolle)

- [H] Definition (Analyse): ein Ledger, der **Entscheidungen, Beweise und Verantwortlichkeit** über den Ablauf hinaus dokumentiert — nicht nur was passierte, sondern warum, auf welcher Evidenz-Basis, durch welchen Agenten, mit welchem Ergebnis und welcher Verifikation [H].
- [F] Anker im Bestand: `decisions`-Tabelle (id, task_id, worker_id, confidence, reasoning, made_at, model_id, source_event_seq; + trace_id, span_id, decision_type, decision_status, governance_action, parent_decision_id) [F: runtime/database.py:93-124]; `validation_artifacts` (validation_id, evaluation_id, execution_id, trace_id, span_id, decision_id, agent_id, model_id, outcome_id, validation_result, evidence_status, rationale, integrity_hash) [F: runtime/database.py:176-189].
- [F] Identity-Felder existieren im Receipt-/Verification-Pfad: trace_id, span_id, decision_id, request_id, plan_id, step_id, agent_id, model_id, cognitive_unit_id, retry_count, attempt_number, _integrity_hash [F: MC-TC-004-POST-REMEDIATION-TRUTH-AUDIT.md:361-384].
- [I] Unterschied in der Systematik: Event Log = Sequenz von Ereignissen (temporal), Cognitive Ledger = **bilanzierende Kette von Claims, Evidenz, Entscheidungen und Verifikationen** (kausal + attributiv + beweisbar) [I: MR „CLAIM ≠ REALITY"].

### 1.3 Gemeinsamkeiten / Überlappung

- [F] Beide sind append-only und replayfähig [F: event_store.py:36-37,305-332].
- [F] Verification-Referenzpfad: `verified` erfordert receipt_id + execution_id (EvidenceRequiredError) [F: event_store.py:202-210] — beweis-gebundener Status bereits im Event-Modell [I].
- [I] Ein Event-Log kann **erweitert** zum Cognitive Ledger werden (additive Metadaten + neue Event-Typen), wenn die Kausal-/Attributions-/Beweis-Kette vollständig wird [I: B2MA §1].

---

## 2. Anforderungen

| Anforderung | Ist-Befund | Lücke |
|-------------|------------|-------|
| **Replay** | [F] vorhanden + MC-TC-006 deterministisch [F: runtime/event_store.py:305-332; PST]; Cursor In-Memory (E-6) [F: features/replay/replay_service.py:20,84-90] | [I] Cursor-Persistenz (E-6) für inkrementelle Pfade [I: ESIA E-6] |
| **Audit** | [F] stored_events append-only + event_id UNIQUE [F: event_store.py:57]; aber kein Ketten-Hash (E-11) [F: event_store.py:50-67]; audit_log nur 30d-Retention [F: features/observability/event_persistence.py:8,33] | [I] Ketten-Integrität (E-11); Dauer-Audit über die 30d-Grenze [I] |
| **Evidence** | [F] store_receipt/store_verification persistieren Receipts + Verifications als Events [F: event_store.py:154-272]; `verified` erfordert receipt_id [F: event_store.py:202-210]; EvidenceRequiredError als Invariante [F] | [I] Evidence-Referenzen als first-class Felder (evidence_ref), Verknüpfung zu muscal/evidence/ (recorder, models) [I: muscal/src/muscal/evidence/] |
| **Agent Attribution** | [F] agent_id/model_id im Receipt-Pfad vorhanden [F: MC-TC-004-POST-REMEDIATION:376-377]; execution_id-Pflicht für Execution-Topics [F: event_store.py:21-32,98-101]; **aber:** keine agent-Spalte in stored_events; source ist Freitext [F: event_store.py:54] | [I] formale Agent-Identität im Event-Schema (attribution); agent-Boundary zwischen CORE-Runtime und muscal/-Verification [I] |
| **Decision History** | [F] `decisions`-Tabelle mit parent_decision_id, decision_type, decision_status, governance_action, source_event_seq [F: runtime/database.py:93-124]; `validation_artifacts` mit decision_id [F: runtime/database.py:176-189] | [I] Entscheidungen sind **Nicht-Events** (eigene Tabellen) — im Ledger-Konzept als Entscheidungs-Events oder referenzierte Artefakte formalisieren [I] |
| **Temporal Queries** | [F] timestamp REAL + created_at ISO + seq-Ordnung [F: event_store.py:51,56,58]; Indizes auf topic/created_at/execution_id [F: event_store.py:70-77]; Edge-Events ohne timestamp (E-9) [F: graph.py:124-128] | [I] Edge-Zeit (E-9), logische Zeit (logical_time), Zeitraum-Abfragen über Projection [I: ESIA E-9, §6] |

---

## 3. Kann B2 Hybrid diese Rolle erfüllen?

### 3.1 Prüf-Ergebnis (Analyse)

| B2-Element | Beitrag zum Cognitive Ledger | Status |
|------------|------------------------------|--------|
| EventStore als Single Truth | [I] Kette aller Execution-Events + (künftig) Evidence-/Decision-Events [I: B2PKG Teil 2] | [F] Basis vorhanden [F: event_store.py:36-37] |
| muscal/ als Verification/Governance-Layer | [I] Claims/Evidence/Verification als Ledger-Bewertungsschicht (CLAIM≠PROOF) [F: MR] | [F] Paket existiert, kein Code-Kontakt [F: STE E1.1/E1.2] |
| Graph Projection | [I] rekonstruierbarer kognitiver Zustand aus Ledger-Events [I: B2MA §2] | [F] Bausteine vorhanden; Rebuild fehlt [F: MC-TC-007:67] |
| Verification Layer | [F] execution.receipt/execution.verification-Events mit Conflict-Guard (VerificationConflictError) [F: event_store.py:181-272] | [F] vorhanden für Execution-Pfad |

- [I] **Bedingtes Ja (Analyse):** B2-Hybrid kann die Cognitive-Ledger-Rolle erfüllen, wenn drei Lücken-Klassen geschlossen werden: (a) Schema-Erweiterung (Attribution, Evidence-Refs, Ketten-Hash), (b) Decision-/Governance-Events statt Nur-Tabellen, (c) Log-Vollständigkeit der Graph-Mutationen [I: §4].
- [F] Ohne diese Erweiterungen ist der EventStore ein Execution Event Log mit Verification-Attributen, aber **kein** vollständiger Cognitive Ledger [I: §1-2-Gegenüberstellung].

### 3.2 Grenzen der Rolle

- [I] Ledger = Dokumentations-/Beweisebene, nicht Ausführungs-Ebene: CORE bleibt Runtime; Ledger protokolliert und attestiert [I: B2PKG Teil 2].
- [I] Beweis-Belastbarkeit ohne Ketten-Hash (E-11) begrenzt (Audit-Integrität) [I: ESIA E-11].
- [F] 30d-Retention des audit_log ungeeignet für Ledger-Zweck (Dauerhaftigkeit) [F: event_persistence.py:8,33].
- [H] Multi-Agent-Tauglichkeit gegeben, sobald Agent-Attribution formalisiert ist (agent_id heute nur im Receipt-Pfad) [H: MC-TC-004-POST-REMEDIATION:376].

---

## 4. Fehlende Event-Typen, Metadaten, Invarianten

### 4.1 Fehlende Event-Typen (Register)

| Event-Typ | Begründung | Referenz |
|-----------|------------|----------|
| `graph.node_updated` mit payload_delta | [I] Inhalts-Treue (E-1) | [F: graph.py:103-108; ESIA E-1] |
| `graph.node_removed` (Tombstone) | [I] Lösch-Historie (E-2) | [F: graph.py:133-138; ESIA E-2] |
| `graph.edge_removed` | [I] Kanten-Löschung (E-3) | [F: graph.py:140-143; ESIA E-3] |
| `graph.pruned` (Pruning-Marker) | [I] Struktur-Grenzen deterministisch (E-4) | [F: graph.py:145-158; ESIA E-4] |
| `graph.focus_changed` | [I] temporaler Zustand (E-5) | [F: graph.py:162-165; ESIA E-5] |
| `execution.failed` im EventStore | [I] Watchdog-Persistenz (E-7/E-8) | [F: execution_watchdog.py:96-119; ESIA E-7/E-8] |
| `decision.*` (decision.created/updated/resolved) | [I] Decision History als Event-Kette (heute Tabelle) | [F: runtime/database.py:93-124] |
| `governance.action` (Policy-Entscheidungen) | [H] Governance-Aktionen als attestierte Events | [H: muscal/src/muscal/governance/] |
| `evidence.attached` / `evidence.verified` | [I] Evidence-Verknüpfung in der Kette | [I: muscal/src/muscal/evidence/] |
| `snapshot.taken` (Kompaktions-Marker) | [I] Snapshot-Historie (E-10) | [F: muscal_os.py:391-397; ESIA E-10] |

### 4.2 Fehlende Metadaten

| Metadatum | Fehlt | Referenz |
|-----------|-------|----------|
| aggregate_id / aggregate_type | [F] in stored_events; nur legacy events [F: event_store.py:50-67; database.py:62-63] | [I: B2MA §1.1] |
| agent_id (Attribution) | [F] nur Receipt-Pfad, nicht Event-Schema [F: event_store.py:50-67; MC-TC-004-POST-REMEDIATION:376] | [I] |
| evidence_refs | [F] keine Evidence-Verknüpfung [F: event_store.py:50-67] | [I] |
| parent_event_id | [F] nur causation_id als Näherung [F: event_store.py:61] | [I: ESIA §6] |
| logical_time | [F] fehlt [F: event_store.py:50-67] | [I: ESIA §6] |
| prev_hash / event_hash | [F] fehlt (E-11) [F: event_store.py:50-67] | [I: ESIA E-11] |
| metadata (frei) | [F] keine Metadaten-Spalte [F: event_store.py:50-67] | [I: B2MA §1.1] |
| decision_ref / validation_ref | [F] Verbindung zu decisions/validation_artifacts fehlt im Event-Modell [F: event_store.py:50-67; database.py:93-124,176-189] | [I] |

### 4.3 Fehlende Invarianten

| Invariante | Ist | Ziel (Analyse) |
|------------|-----|----------------|
| Ketten-Integrität | [F] fehlt (kein Hash) [F: event_store.py:50-67] | [H] prev_hash-Verkettung; Manipulation erkennbar (E-11) |
| Event-Vollständigkeit der Mutationen | [F] remove/prune/focus ohne Events [F: graph.py:133-165] | [H] jede Zustands-Mutation erzeugt genau ein Event (Mutation→Event-Bijektion) |
| Agent-Attributions-Pflicht | [F] nicht im Schema [F: event_store.py:50-67] | [H] Agent-Events ohne agent_id ablehnen (analog execution_id-Pflicht [F: event_store.py:98-101]) |
| Claim/Proof-Bindung | [F] vorhanden für „verified" (receipt_id-Pflicht) [F: event_store.py:202-210] | [I] auf Decision-/Governance-Events ausweiten [I] |
| Entscheidungs-Aktualität | [F] decision_status als Spalte, kein Zustands-Übergangs-Zwang [F: database.py:105] | [H] Zustands-Übergänge (proposed→accepted→…) als Events mit Vorgänger-Pflicht |
| Konsistenz der drei Speicher | [F] kein Abgleich-Mechanismus [F: runtime/kernel/writer.py:110-175; ESIA §2.1] | [I] Projektions-Invariant: stored_events als einzige Wahrheit [I: B2PKG Teil 3] |

---

## 5. Mapping: CORE / muscal/ / EventStore / Graph Projection / Verification Layer

| Ebene | Rolle im Cognitive Ledger | Beleg | Nicht-Rolle |
|-------|---------------------------|-------|-------------|
| **CORE (Execution Runtime)** | [I] erzeugt Execution-Events (Kernel, Tools, Watchdog) [F: kernel.py:133-157; execution_watchdog.py:96-119]; bleibt Ausführungsebene | [F: kernel.py:163-169; B2PKG Teil 2] | keine Ledger-Verwaltung, keine Verification-Autorität [I: ADR-011; SR] |
| **muscal/ (Integrity/Governance)** | [I] Claims/Evidence/Verification/Governance als Bewertungsschicht; Module verification/, evidence/, governance/, claims/, reality/ [F: muscal/src/muscal/] | [F: MR; B2PKG Teil 2] | keine Execution, kein Zustands-Mutation [I] |
| **EventStore (Ledger-Kern)** | [I] append-only Wahrheit: Execution-Events + künftig Decision-/Evidence-/Governance-Events + Ketten-Hash [I: B2MA §1] | [F: event_store.py:36-37; B2PKG Teil 2] | keine Projektion, keine Berechnung [I: D-008] |
| **Graph Projection** | [I] rekonstruierter kognitiver Zustand aus Ledger (add_node/update_node/add_edge via public API) [I: B2MA §2] | [F: graph.py:61-108; _replaying graph.py:56,226-229] | kein Autor, keine Wahrheit [I: B2PKG Teil 2] |
| **Verification Layer** | [F] attestiert Claims → execution.verification-Events mit receipt-Bindung [F: event_store.py:181-272]; muscal/-Verification als ausführende Instanz [F: MR] | [F: event_store.py:202-210; MC-TC-004-POST-REMEDIATION:317,361-384] | keine Zustands-Mutation am Graph [I] |

- [F] Heutige Konstellation: Verification-Orchestrator schreibt execution.verification (Source „VerificationOrchestrator") [F: event_store.py:252] — eine Instanz, die im B2-Modell durch muscal/-Layer formalisiert würde [I].
- [I] Datenfluss-Ziel (Analyse): CORE erzeugt Events → EventStore ist Kette → Projection baut Zustand → muscal/ bewertet (Claims→Evidence→Verification) → attestierte Ergebnisse fließen als Events zurück in die Kette [I: B2PKG Teil 3/5].

---

## Validation

- Read-only: keine Datei verändert (außer dieser neuen), kein Commit, keine Implementierung, keine Entscheidung, keine Empfehlung als Fakt.
- Alle [F] mit Datei:Zeile bzw. Artefakt-Referenz; [H]-Aussagen (Ledger-Definition, Event-Typen, Invarianten, Mapping-Ziel) als Analyse-Spielraum gekennzeichnet.
- Konsistent mit ESIA/STE/B2PKG/B2MA, SESSION_RULES v2.0, DECISION_REGISTRY, PROJECT_STATE; Statuslage unverändert.

**Ende nach Erstellung** — keine weiteren Aktionen.
