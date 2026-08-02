# MINIMAL_COGNITIVE_LEDGER_SPECIFICATION

Minimale Erweiterung von MUSCAL EventStore zum Cognitive Ledger — Spezifikations-Grundlage

- Datum: 02.08.2026
- Modus: **READ ONLY** — nur Analyse, keine Codeänderung, kein Commit, keine automatische Entscheidung, keine Empfehlung als Fakt
- Kennzeichnung: [F] FACT (Datei:Zeile) · [I] INFERENCE · [H] HYPOTHESIS
- Zweck: Definition des **minimalen** Erweiterungsumfangs (kein Vorschlag für Voll-Ausbau); Grundlage für künftige ADR-/Review-Entscheidungen
- Quellen: COGNITIVE_LEDGER_ARCHITECTURE_REVIEW.md [CLAR], EVENT_SOURCING_INTEGRITY_ANALYSIS.md [ESIA], B2_HYBRID_MIGRATION_ANALYSIS.md [B2MA], B2_HYBRID_ARCHITECTURE_DECISION_PACKAGE.md [B2PKG], STATE_TRANSITION_EVENT_ANALYSIS.md [STE], SESSION_RULES v2.0 [SR], DECISION_REGISTRY.md [REG], PROJECT_STATE.md [PST], Code-Stand 02.08.2026
- Status: **created, not committed (external KF layer)**

---

## 1. Minimal notwendige neue Event-Typen

> Auswahl-Kriterium „minimal": nur Event-Typen, ohne die die Cognitive-Ledger-Funktionen (Evidence, Attribution, Decision History, Audit) nicht erfüllbar sind [I: CLAR §4.1].

### 1.1 Entscheidungs-Events

| Event | Zweck | Anker-Referenz |
|-------|-------|----------------|
| `decision.created` | [H] Entscheidung als Ledger-Event statt Nur-Tabelle (heute `decisions`-Tabelle [F: runtime/database.py:93-124]) | [I: CLAR §4.1] |
| `decision.updated` / `decision.resolved` | [H] Zustands-Übergänge mit Vorgänger-Pflicht (parent_decision_id existiert in Tabelle [F: database.py:107]) | [I: CLAR §4.3] |

- [F] Heute: decisions/validation_artifacts sind **Nicht-Events** (eigene Tabellen, database.py:93-124,176-189) [F] — minimale Erweiterung: Entscheidungs-Zustandswechsel als Events **zusätzlich** zur Tabelle (Tabelle bleibt Lese-Projektion) [H].

### 1.2 Evidence-Events

| Event | Zweck | Anker-Referenz |
|-------|-------|----------------|
| `evidence.attached` | [H] Beweis-Stück an Claim/Execution binden | [I: muscal/src/muscal/evidence/ (recorder, models)] |
| `evidence.verified` | [H] Beweis-Prüfung als attestiertes Event | [I: CLAR §4.1] |

- [F] Verifikations-Referenzpfad existiert: `execution.verification` mit `verified`-Pflicht auf receipt_id+execution_id [F: runtime/event_store.py:202-210] — Evidence-Events können dieses Muster verallgemeinern [I].

### 1.3 Verification-Events (Minimal-Erweiterung)

- [F] `execution.verification` / `execution.receipt` existieren bereits [F: event_store.py:154-272]; `VERIFICATION_PASSED`/`VERIFICATION_FAILED` in _EXECUTION_REQUIRED_TOPICS [F: event_store.py:30-31].
- [H] Minimal zusätzlich: `verification.evidence_required` (bei fehlender Evidence) als explizites Ledger-Ereignis [H] — oder Verzicht, da EvidenceRequiredError als Exception existiert [F: event_store.py:202-210] [I].
- [I] Bewertung: **Verification ist als Basis vorhanden**; Erweiterung minimal (Attribution + Evidence-Refs, s. §2) [I].

### 1.4 Agent-Events

| Event | Zweck | Anker-Referenz |
|-------|-------|----------------|
| `agent.registered` | [H] Agent-Identität im Ledger etablieren (Attributions-Basis) | [F: agent_id nur im Receipt-Pfad, MC-TC-004-POST-REMEDIATION:376; ESIA §2] |
| `agent.action_authorized` / `agent.action_denied` | [H] Policy-Entscheidungen je Agent | [I: muscal/src/muscal/governance/; CLAR §4.1] |

- [I] Ohne Agent-Registrierung ist Attribution nicht verifizierbar [I: CLAR §2/§4.2].

### 1.5 State Transition Events (Minimal)

| Event | Zweck | Anker-Referenz |
|-------|-------|----------------|
| `graph.node_updated` mit payload_delta | [I] Inhalts-Treue (E-1) — Pflicht für Inhalts-Rekonstruktion | [F: graph.py:103-108; ESIA E-1] |
| `graph.node_removed` / `graph.edge_removed` | [I] Lösch-Historie (E-2/E-3) | [F: graph.py:133-143; ESIA E-2/E-3] |
| `graph.pruned` | [I] Pruning-Marker (E-4) | [F: graph.py:145-158; ESIA E-4] |
| `graph.focus_changed` | [I] temporaler Zustand (E-5) | [F: graph.py:162-165; ESIA E-5] |
| `execution.failed` (EventStore-append) | [I] Watchdog-Persistenz (E-7/E-8) | [F: execution_watchdog.py:96-119; ESIA E-7/E-8] |

- [F] Diese Typen sind die Graph-Evolutions-Gaps aus B2MA §2 [F: B2MA §2; ESIA §5].

### 1.6 Governance-Events

| Event | Zweck | Anker-Referenz |
|-------|-------|----------------|
| `governance.policy_decision` | [H] Policy-/Governance-Aktionen als attestierte Events | [I: muscal/src/muscal/governance/ (governor, conflict, consensus)] |
| `governance.overridden` | [H] OVERRIDE-Pfad (D-020) als Ledger-Ereignis | [F: SR D-020; AGENTS.md OVERRIDE-Pfad] |

- [I] Governance-Events sind Minimal-Element, wenn muscal/ Governance-Layer wird [I: B2PKG Teil 2]; ohne Layer-Beschluss zurückstellbar [I].

---

## 2. Minimal notwendige Schema-Erweiterungen

| Feld | Spalte | Notwendigkeit | Beleg |
|------|--------|---------------|-------|
| aggregate_id | [I] zielgerichtete Rekonstruktion | **MUSS** [I: CLAR §4.2] | [F: fehlt in stored_events, event_store.py:50-67; vorhanden in legacy, database.py:62] |
| aggregate_type | [I] Aggregat-Klassifikation | **MUSS** (mit aggregate_id) [I] | [F: database.py:63] |
| agent_id | [I] Attribution | **MUSS** [I: CLAR §2/§4.2] | [F: nur Receipt-Pfad, MC-TC-004-POST-REMEDIATION:376] |
| evidence_refs | [I] Evidence-Verknüpfung | **MUSS** für Evidence-Funktion [I: CLAR §2] | [F: fehlt, event_store.py:50-67] |
| parent_event_id | [I] explizite Kausal-Kette | **MUSS** (causation_id reicht nicht für Kette) [I: CLAR §4.2] | [F: causation_id als Näherung, event_store.py:61] |
| prev_hash / event_hash | [I] Ketten-Integrität (E-11) | **MUSS** für Audit-Belastbarkeit [I: CLAR §2] | [F: fehlt, event_store.py:50-67] |
| metadata (JSON) | [I] Pruning-/Focus-/Temporal-Info (E-4/E-5/E-9) | **SOLLTE** (alternative: payload-Subfelder) [I] | [F: fehlt, event_store.py:50-67] |
| logical_time | [I] Monotonie unabhängig von wall-clock | **Nice-to-have** (seq erfüllt Ordnung) [I: ESIA §6] | [F: fehlt, event_store.py:50-67] |
| decision_ref / validation_ref | [I] Verbindung zu decisions/validation_artifacts | **SOLLTE** (bei §1.1-Umsetzung) [I] | [F: Tabellen existieren, database.py:93-124,176-189] |
| event_source_scope | [I] formaler Erzeuger-Scope (CORE/muscal/Bridge) | **Nice-to-have** (source als Freitext [F: event_store.py:54]) | [H: B2MA §1.1] |

- [F] Migrations-Muster additiv/idempotent vorhanden: `_migrate_add_columns` [F: event_store.py:274-303]; `schema_version`-Inkrement [F: event_store.py:65,143].
- [F] MCPL-Spezifikation plant bereits Schema-Erweiterung — Überschneidung prüfen [F: spec/MC-006-MCPL-TECHNICAL-SPECIFICATION.md:81-86,1481].

---

## 3. Muss-Felder vs Nice-to-have

### MUSS (Pflicht für Ledger-Funktion)

| Feld | Begründung |
|------|------------|
| aggregate_id + aggregate_type | [I] Rekonstruktion + Projection-Regeln [I: CLAR §2] |
| agent_id | [I] Attribution ohne Freitext-Source [I: CLAR §2/§4.2] |
| evidence_refs | [I] Evidence-Funktion nicht abbildbar ohne Verknüpfung [I] |
| parent_event_id | [I] Kausal-Kette über causation_id hinaus [I] |
| prev_hash / event_hash | [I] Audit-Integrität (E-11) [I] |
| payload_delta (bei graph.node_updated) | [I] Inhalts-Rekonstruktion (E-1) [I: ESIA E-1] |

### SOLLTE (funktionsstärkend, zurückstellbar)

| Feld | Begründung |
|------|------------|
| metadata | [I] saubere Trennung vs. payload-Verschmutzung (E-4/E-5/E-9) [I] |
| decision_ref / validation_ref | [I] Ledger-Verknüpfung zu bestehenden Tabellen [I] |
| snapshot_seq-Anker | [I] Snapshot-Format-Resume (B2MA §3.1) [I] |

### NICE-TO-HAVE (später)

| Feld | Begründung |
|------|------------|
| logical_time | [I] seq deckt Ordnung ab [I: ESIA §6] |
| event_source_scope | [I] Boundary-Prüfung via source möglich [H] |
| retry_count / attempt_number (als Event-Spalten) | [F] existieren im Receipt-Pfad [F: MC-TC-004-POST-REMEDIATION:379-380]; Ledger-Spalten optional [I] |

- [I] Muss-Kriterium: ohne das Feld ist mindestens eine der Anforderungen Replay/Audit/Evidence/Attribution/Decision-History/Temporal-Queries (CLAR §2) nicht erfüllbar [I: CLAR §2].

---

## 4. Invarianten

### 4.1 Replay

- [F] Bestehende Invariante: `seq > cursor ORDER BY seq ASC` — deterministisch [F: event_store.py:305-332]; event_id UNIQUE [F: event_store.py:57]; `_replayed`-Suppression [F: event_store.py:94-95,112-119].
- [I] Zusätzlich: Cursor-Persistenz (E-6) für inkrementelle Pfade [I: ESIA E-6].
- [H] Invariante 1 (Ziel): „Replay(events, cursor) ist deterministisch und idempotent; ein Event erscheint genau einmal im Rebuild-Pfad." [H]

### 4.2 Audit

- [F] append-only + IntegrityError bei Duplikat [F: event_store.py:57,84-85]; aber kein Ketten-Hash [F: event_store.py:50-67].
- [H] Invariante 2 (Ziel): „Jedes Event trägt prev_hash; die Kette ist rekursiv verifizierbar (seq n ⇒ hash(n-1))." [H: ESIA E-11]
- [F] audit_log-30d-Retention ist für Ledger ungeeignet [F: features/observability/event_persistence.py:8,33] — Audit-Invariante liegt auf stored_events, nicht audit_log [I].

### 4.3 Attribution

- [H] Invariante 3 (Ziel): „Jedes Agent-/Decision-/Verification-/Governance-Event trägt agent_id; ohne agent_id wird der append abgelehnt" (Muster: execution_id-Pflicht [F: event_store.py:98-101]). [H: CLAR §4.3]

### 4.4 CLAIM≠PROOF

- [F] Bestehende Invariante: `verified` erfordert receipt_id + execution_id (EvidenceRequiredError) [F: event_store.py:202-210]; VerificationConflictError bei Status-Konflikt [F: event_store.py:225-230].
- [H] Invariante 4 (Ziel): „Ein Event mit verification_state='verified' MUSS referenzierte Evidence vorweisen; CLAIM (unverified) ist immer möglich, PROOF (verified) nie ohne Beleg." [H: event_store.py:202-210-Muster]

### 4.5 Mutation→Event

- [F] Heute verletzt: remove_node/remove_edge/prune_graph/set_focus ohne Event [F: graph.py:133-165]; NODE_UPDATED ohne Delta [F: graph.py:103-108].
- [H] Invariante 5 (Ziel): „Jede GraphState-Mutation erzeugt genau ein korrespondierendes Event; Rebuild(Events) ≡ Zustand (Bijektion)." [H: CLAR §4.3]

---

## 5. Mapping

### 5.1 EventStore v1 → v2 (Schema-/Semantik-Erweiterung)

| v1 (heute) | v2 (minimal) | Beleg |
|------------|--------------|-------|
| Execution-Topics + receipts/verifications | [I] + Decision-/Evidence-/Governance-/Agent-/State-Transition-Events (§1) | [F: event_store.py:50-67,154-272] |
| Identitäts-Felder (execution/correlation/causation) | [I] + aggregate_id/-type, agent_id, evidence_refs, parent_event_id, prev_hash (§2) | [F: event_store.py:59-61; CLAR §4.2] |
| `_EXECUTION_REQUIRED_TOPICS`-Pflicht | [I] + Attributions-/Ketten-Pflichten (Invarianten 3/2) | [F: event_store.py:21-32,98-101] |
| migration additiv | [I] Schema v2 additiv via `_migrate_add_columns`-Muster; schema_version=2 | [F: event_store.py:274-303,65,143] |

- [F] V2 ist **additive Erweiterung**, kein Neubau: bestehende Events bleiben lesbar/replaybar [I: B2MA §1.2].

### 5.2 CORE Runtime

- [F] CORE erzeugt weiterhin Execution-Events; Kernel/Tools/Watchdog unverändert als Erzeuger [F: kernel.py:133-157; execution_watchdog.py:96-119].
- [I] CORE liefert zusätzlich payload_delta bei update_node (E-1) — CORE-Berührung (graph.py, D-020) nur via OVERRIDE oder features/-Projektionsweg [I: B2MA §4.2; SR].
- [I] CORE ist **kein** Ledger-Konsument; bleibt Ausführungsebene [I: B2PKG Teil 2].

### 5.3 muscal Verification Layer

- [I] muscal/ konsumiert Ledger-Events (claims/evidence/verification), bewertet und schreibt attestierte Ergebnisse als Events zurück (evidence.verified, execution.verification-Muster) [I: muscal/src/muscal/verification/, evidence/; event_store.py:181-272].
- [I] Agent-/Policy-Events (§1.4/§1.6) entstehen im Governance-Layer (muscal/governance) [I: muscal/src/muscal/governance/].
- [F] Integrationsvertrag CORE↔muscal/ fehlt (kein Code-Kontakt) [F: STE E1.1/E1.2] — Vertrag ist Voraussetzung, nicht Teil der Spezifikation [I].

### 5.4 Graph Projection

- [I] Projection liest Ledger (Store → Replay → public GraphState-API) und baut Zustand; `_replaying`-Flag als Mechanismus vorhanden [F: graph.py:56,226-229; B2MA §2].
- [I] Rebuild-Treue heute Struktur ≈78 %, Zustand ≈46 % [I: STE §4] — Zielwerte sind Human-Entscheidung, nicht Spezifikations-Gegenstand [I].
- [F] Rebuild-Service fehlt [F: MC-TC-007_STATUS_ZUSAMMENFASSUNG.md:67] — gehört zur Implementierung, nicht zur minimalen Schema-Spezifikation [I].

---

## 6. Produktions-Gate

> Kriterien, die für den Ledger-Betrieb erfüllt sein müssen (Checkliste — keine Freigabe-Autorität).

| # | Kriterium | Bezug | Prüfbar via |
|---|-----------|-------|-------------|
| G1 | Schema v2-Felder additiv migriert, Bestands-Events unverändert | §2; [F: event_store.py:274-303] | Zeilen/seq-Kontinuität vor/nach |
| G2 | Invariante 1 (Replay deterministisch + idempotent) | §4.1; [F: MC-TC-006] | MC-TC-006-Rerun ±0 [F: POST_ARB_EXECUTION_PLAN 4.3] |
| G3 | Invariante 4 (CLAIM≠PROOF: verified ⇒ Evidence) | §4.4; [F: event_store.py:202-210] | Negativ-Tests (append ohne receipt → EvidenceRequiredError) |
| G4 | Invariante 5 (Mutation→Event-Bijektion) | §4.5 | Rebuild ≡ Zustand-Test (E-10-Mechanismus) |
| G5 | Attributions-Pflicht (Invariante 3) aktiv | §4.3 | append-Test ohne agent_id (Agent-Events) |
| G6 | Ketten-Hash aktiv (Invariante 2) | §4.2 | Verifikations-Skript über seq-Kette |
| G7 | Graph-Gaps geschlossen (E-1…E-5, E-7/E-8) | §1.5; [F: ESIA §5] | Event-Vollständigkeits-Tests je Mutation |
| G8 | Decision-/Evidence-Events durchgehend (sofern §1.1/§1.2 beschlossen) | §1 | Ledger-Ablauf-Test (Claim→Evidence→Decision→Verification) |
| G9 | Audit über stored_events (nicht audit_log-30d) | §4.2; [F: event_persistence.py:8,33] | Abfrage-Äquivalenz über Ledger-Events |
| G10 | MC-TC-007 Phase-H-Ziel (Rebuild-Validierung) | [F: MC-TC-007:67] | Rebuild-Validierungs-Test + Kennzahl |

- [I] Gate-Kriterien sind **Annahme-Kriterien** für den Ledger-Betrieb; Freigabe-Beschluss liegt bei Human (Decision Owner) [I: HUMAN_DECISION_INDEX].
- [F] Voraussetzungen außerhalb der Spezifikation: RC-1a/RC-1b-Entscheidung, RC-2 (HDR-001), RC-4a (ADR-Review) [F: RC6_MEASUREMENT_GATE_CHECKLIST].

---

## Validation

- Read-only: keine Datei verändert (außer dieser neuen), kein Commit, keine Implementierung, keine Entscheidung, keine Empfehlung als Fakt.
- Alle [F] mit Datei:Zeile bzw. Artefakt-Referenz; [H]-Aussagen (Event-Typen, Invarianten, Gate-Kriterien) als Spezifikations-Vorschlag gekennzeichnet, kein Beschluss.
- Konsistent mit CLAR/ESIA/B2MA/B2PKG/STE, SESSION_RULES v2.0, DECISION_REGISTRY, PROJECT_STATE; Statuslage unverändert.

**Ende nach Erstellung** — keine weiteren Aktionen.
