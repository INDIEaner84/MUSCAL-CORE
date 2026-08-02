# COGNITIVE_LEDGER_MIGRATION_RISK_ASSESSMENT

Risiko-Bewertung der Migration EventStore v1 → Cognitive Ledger v2

- Datum: 02.08.2026
- Modus: **READ ONLY** — nur Analyse, keine Codeänderung, kein Commit, keine automatische Entscheidung
- Kennzeichnung: [F] FACT (Datei:Zeile) · [I] INFERENCE · [H] HYPOTHESIS
- Basis: MINIMAL_COGNITIVE_LEDGER_SPECIFICATION.md [MCLS], COGNITIVE_LEDGER_IMPLEMENTATION_CONTRACT.md [CLIC], COGNITIVE_LEDGER_ARCHITECTURE_REVIEW.md [CLAR], EVENT_SOURCING_INTEGRITY_ANALYSIS.md [ESIA], B2_HYBRID_MIGRATION_ANALYSIS.md [B2MA], SESSION_RULES v2.0 [SR], PROJECT_STATE.md [PST], Code-Stand 02.08.2026
- Status: **created, not committed (external KF layer)**

---

## 1. Datenmigration

### 1.1 Bestehende stored_events (Kern-Bestand)

- [F] Bestand: append-only-Tabelle mit 17 Spalten; event_id UNIQUE, seq AUTOINCREMENT [F: runtime/event_store.py:50-67].
- [F] Migrations-Muster additiv/idempotent vorhanden: `_migrate_add_columns` (PRAGMA-basiert, ALTER TABLE ADD COLUMN) [F: runtime/event_store.py:274-303] — v2-Spalten (aggregate_id, agent_id, evidence_refs, parent_event_id, prev_hash, metadata) [I: MCLS §2] werden so additiv angelegt [I].
- [I] **Bestands-Zeilen bleiben physisch unverändert** — kein Rewrite, kein seq-Bruch [I: event_store.py:328].
- [H] Historische Zeilen tragen Defaults (''/leere JSON) für neue Spalten — semantisch „unattribuiert"; Rückwirkende Befüllung wäre separate Entscheidung (nicht Teil des Minimal-Umfangs) [H: MCLS §3].
- [F] Risiko-Charakter: niedrig bis mittel — reine ALTER-Operation; DB-Lock kurz [I]; aber zwei SQLite-Verbindungen auf eine Datei (MuscalOS + WriterThread) [F: spec/ADRs/ADR-EVENT-001-eventstore-boundary.md:17-20] — Lock-Konkurrenz bei paralleler Migration möglich [I].

### 1.2 Legacy `events`-Tabelle

- [F] WriterThread schreibt canonical in stored_events **und** derived in `events` (idempotency_key UNIQUE, aggregate_id/aggregate_type vorhanden) [F: runtime/kernel/writer.py:44-46,110-175; runtime/database.py:53-71].
- [F] `events` enthält überlappende und nicht-überlappende Ereignisse (kein Reconcile-Mechanismus) [F: MC-TC-004-POST-REMEDIATION-TRUTH-AUDIT.md:540].
- [I] Migration betrifft `events` nicht direkt (bleibt derived-Parallel-Spur) — **Risiko: Doppel-Wahrheit bleibt bestehen**, wenn keine Ablösung entschieden wird [I: ESIA §2.1; CLIC §2 Phase 2-Risiko].
- [I] Optionen (Analyse, kein Beschluss): weiterführen als Lese-Kompatibilitäts-Schicht, Abschaltung als eigene Entscheidung [I: B2MA §1.2].

### 1.3 audit_log

- [F] audit_log: entry_type, payload, created_at [F: runtime/database.py:166-169]; 30d-Retention mit Löschung [F: features/observability/event_persistence.py:8,29-38].
- [F] audit_log ist **kein** Migrationsziel — Ledger-Audit liegt auf stored_events (MCLS §4.2/§6 G9) [I].
- [I] Risiko: **Vertrauen in audit_log als Dauer-Audit ist bereits heute falsch** (Löschung nach 30d); keine Migration nötig, aber Klarstellung der Rolle [I: CLAR §3.2].

### 1.4 Alte Replay-Daten

- [F] Replay liest stored_events (seq > cursor ORDER BY seq ASC) [F: event_store.py:305-332]; ReplayService-Cursor In-Memory [F: features/replay/replay_service.py:20,84-90].
- [I] Alte Events sind nach v2-Migration unverändert replaybar (Schema-Erweiterung additiv, Replay-Pfad unberührt) [I].
- [I] Aber: Alte Events ohne payload_delta/agent_id können Rebuild-Treue nicht liefern (Inhalts-/Attributions-Lücken bei Bestands-Daten) [I: MCLS §4; CLAR §3.1].
- [F] Misch-Daten (v1-Zeilen + v2-Zeilen) sind für Replay kein Problem (einheitliche Tabelle); semantische Lücken bleiben [I].

---

## 2. Kompatibilität

| Aspekt | Befund | Bewertung |
|--------|--------|-----------|
| Alte Events lesbar | [F] Schema additiv; SELECT-Mapping `_row_to_dict` [F: event_store.py:366-390] bleibt gültig | [I] niedriges Risiko |
| Neue Schema-Version | [F] schema_version-Spalte (Default 1) [F: event_store.py:65]; v2-Inkrement [I: MCLS §2] | [I] Alte Konsumenten ohne schema_version-Check bleiben kompatibel [I] |
| Replay-Mischbetrieb v1/v2 | [F] Replay ordnet nach seq, topic-Filter optional [F: event_store.py:319-329] | [I] v1- und v2-Events in einem Batch — Konsumenten müssen mit leeren neuen Feldern umgehen (Default-Handling) [I: event_store.py:381-389] |
| `_replayed`-Suppression | [F] Duplikat-append wird suppressiert [F: event_store.py:94-95,112-119] | [I] unverändert gültig |
| WriterThread-Kompatibilität | [F] `_map_to_stored_event` [F: runtime/kernel/writer.py:82-103] ohne neue Felder | [I] Writer schreibt weiter v1-artig; v2-Felder nur wenn Mapping erweitert wird (Phase 2) [I] |
| Verifikations-Pfad | [F] store_verification mit receipt-Pflicht [F: event_store.py:202-210] | [I] unverändert; v2-Events konsumieren das Muster [I] |

- [I] Kernaussage: **Rückwärts-Kompatibilität ist durch additiven Ansatz gewahrt**; Restrisiko liegt in Konsumenten, die neue Felder erwarten (dürfen erst nach Freigabe), nicht in Bestands-Pfaden [I: B2MA §1.2].

---

## 3. Performance

| Aspekt | Ist-Befund | v2-Auswirkung (Analyse) |
|--------|------------|-------------------------|
| Eventgröße | [F] payload TEXT (JSON) [F: event_store.py:53]; Receipt-/Verification-Payloads enthalten Identity-Felder [F: MC-TC-004-POST-REMEDIATION:361-384] | [I] neue Spalten (aggregate_id, agent_id, evidence_refs, metadata) erhöhen Zeilenbreite; metadata/payload_delta können Events vergrößern [I] |
| Replay-Zeit | [F] SQL-Scan mit seq-Ordnung, LIMIT-Batching [F: event_store.py:328-332]; ReplayService-Batch 100 [F: features/replay/replay_service.py:28-30] | [I] linear mit Eventzahl; größere Zeilen → langsamer; Indizes vorhanden auf topic/created_at/execution_id [F: event_store.py:70-77], neue Filter (aggregate_id) benötigen neue Indizes [I] |
| Snapshot-Intervalle | [F] kein Snapshot-Mechanismus [F: muscal_os.py:391-397; ESIA E-10] | [H] Snapshot-Frequenz als Funktion von: Rebuild-Kosten (linear), Historie-Wachstum, Start-Latenz — Intervalle sind Betriebs-Entscheidung, nicht Spezifikation [H: B2MA §3] |
| Speicherwachstum | [F] Single-File-SQLite; audit_log 30d-Prune [F: event_persistence.py:8,33]; _update_stream unbegrenzt in-memory [F: graph.py:54,220-223] | [I] v2 = mehr Daten je Event (Metadata, Hash, Evidence-Refs); Dauer-Audit auf stored_events (kein 30d-Prune) wächst unbefristet — Größen-Planung nötig [I] |
| Graph-Limits | [F] MAX_NODES 5000 / MAX_EDGES 10000 [F: graph.py:41-42]; EventBus-Historie 50000 [F: event_bus.py:40] | [I] Projection-Kosten bleiben an Graph-Limits gekoppelt; Snapshot entkoppelt Rebuild von Bestand [I] |

- [I] Performance-Risiko gesamt: **mittel** — linear skalierend, kein neuer Algorithmus; kritisch nur bei unbefristetem Dauer-Audit ohne Snapshot/Kompaktion [I].

---

## 4. Sicherheit

| Aspekt | Befund | Risiko-Bewertung |
|--------|--------|------------------|
| prev_hash / Ketten-Integrität | [F] fehlt heute [F: event_store.py:50-67]; v2 führt prev_hash/event_hash ein [I: MCLS §2/§4.2] | [I] Einführung bei Bestands-Daten: **Anker-Problem** — erste v2-Zeile nach v1-Bestand braucht Hash-Basis (z. B. Hash des letzten v1-Events als Genesis); sonst Kettenlücke [H: CLAR §4.2] |
| Manipulation | [F] heute erkennbar nur über event_id-Duplikate (IntegrityError [F: event_store.py:84-85]); Löschung/Änderung einzelner Zeilen nicht erkennbar [I] | [I] ohne prev_hash bleibt v1-Bestand ungeschützt; erst ab v2-Einführung ist Tampering detektierbar — **Teilschutz** [I: ESIA E-11] |
| Attribution | [F] agent_id nur im Receipt-Pfad [F: MC-TC-004-POST-REMEDIATION:376]; source ist Freitext [F: event_store.py:54] | [I] v2-Attributions-Pflicht (append ohne agent_id → Fehler [I: MCLS §4.3]) gilt nur für neue Agent-Events; Bestands-Events bleiben unattribuiert [I] |
| Evidence Chain | [F] verified ⇒ receipt_id-Pflicht [F: event_store.py:202-210]; EvidenceRequiredError [F: event_store.py:204-210] | [I] v2-Evidence-Refs (evidence_refs) verlängern die Kette; Sicherheit hängt an korrekter Referenz-Auflösung (verwaiste Ref-Verhalten definieren) [H: MCLS §1.2] |
| Zugriff | [F] SQLite-Datei (storage/muscal.db) — Datei-Ebene Schutz [I]; zwei Verbindungen [F: ADR-EVENT-001:17-20] | [I] unverändert durch v2; Hash-Kette macht Manipulation erkennbar, nicht unmöglich [I] |

- [I] Sicherheits-Risiko gesamt: **mittel** — v2 schützt neue Daten (Kette ab Genesis-Punkt), Bestands-Daten bleiben ungeschützt; Genesis-Hash-Entscheidung ist Voraussetzung für durchgängige Kette [H].

---

## 5. Rollback

| Szenario | Möglichkeit | Detail |
|----------|-------------|--------|
| Phase 1 abbrechen (während Migration) | [I] ja — ALTER-Operationen idempotent; Abbruch hinterlässt ggf. einzelne neue Spalten (harmlos, Defaults) [I: event_store.py:274-303] | [I] kein Datenverlust; Bestands-Zeilen unberührt [I] |
| Schema zurück (v2 → v1) | [I] **nicht empfohlen** — SQLite-Drop-Spalte erfordert Table-Rebuild (Copy-Ansatz); kostspielig und fehleranfällig bei großen Beständen [I] | [I] pragmatisch: Spalten unbenutzt lassen, schema_version-Flag „2-deaktiviert" als Rückweg [H: CLIC §2 Phase 1] |
| Daten erhalten | [F] append-only-Doktrin [F: event_store.py:36-37] — kein Löschen im Normalbetrieb | [I] Migration ist daten-erhaltend durch Design (additiv) [I] |
| v2-Funktionen deaktivieren | [I] ja — neue Validierungen (Attributions-Pflicht) abschaltbar via Konfiguration; features/-Plugins deaktivierbar (Plugin-System) [I: CLIC §2] | [I] Rückweg = Funktions-Deaktivierung statt Schema-Revert [I] |

- [I] Rollback-Gesamt: **einfach für Funktionen, schwierig für Schema** — Design-Entscheidung: additiv + deaktivierbar halten, kein Revert-Versuch [I: CLIC §2].

---

## 6. Produktionsrisiken (Register)

| ID | Risiko | Stufe | Begründung | Mitigation (Analyse) | Status |
|----|--------|-------|------------|----------------------|--------|
| PR-1 | Doppel-Wahrheit (stored_events vs. legacy events) bleibt bestehen | **CRITICAL** | [F] kein Reconcile-Mechanismus [F: MC-TC-004-POST-REMEDIATION:540]; Verifikations-/Audit-Pfade können unterschiedliche Ergebnisse liefern [I: ESIA §2.1] | Ablösungs-Entscheidung für legacy `events`; Reconcile-Test als Gate [I] | offen |
| PR-2 | Rebuild-Treue ohne Log-Vollständigkeit (E-1…E-5) | **HIGH** | [F] Struktur ≈78 %, Zustand ≈46 % [I: STE §4]; Mutationen ohne Events [F: graph.py:133-165] | Phase-2-Gap-Schluss vor Projection; Rebuild-Validierung (E-10) [I: MCLS §6 G4] | offen |
| PR-3 | Ketten-Lücke beim Genesis-Hash (v1-Bestand ohne Hash) | **HIGH** | [F] kein prev_hash heute [F: event_store.py:50-67] | Genesis-Hash über letzten v1-Event; klare Schutzgrenze dokumentieren [H: §4] | offen |
| PR-4 | Dauer-Audit-Wachstum ohne Kompaktion | **MEDIUM** | [I] unbefristete stored_events-Nutzung; kein Snapshot [F: muscal_os.py:391-397] | Snapshot (Phase 4) + Archivierungspolitik [I] | offen |
| PR-5 | Replay-Performance-Abfall durch größere Events + neue Filter | **MEDIUM** | [I] Zeilenbreite steigt; neue Indizes nötig [I: §3] | Indizes (aggregate_id), Batch-Größen, Last-Test [I] | offen |
| PR-6 | Attributions-Lücke bei Bestands-Events | **MEDIUM** | [F] historische Zeilen ohne agent_id [F: event_store.py:50-67] | Pflicht nur für neue Events; Altdaten als „unattribuiert" kennzeichnen [I] | offen |
| PR-7 | Lock-Konkurrenz bei Migration (zwei Verbindungen) | **MEDIUM** | [F] zwei SQLite-Verbindungen auf eine Datei [F: ADR-EVENT-001:17-20] | Migration bei ruhendem System; WAL/Backup vorab [I] | offen |
| PR-8 | audit_log-Fehlvertrauen (30d-Löschung) | **MEDIUM** | [F] Retention-Löschung [F: event_persistence.py:8,33] | Rollen-Klarstellung: Audit = stored_events [I: MCLS §6 G9] | offen |
| PR-9 | Performance durch Verification Layer (muscal/-Integration) | **MEDIUM** | [F] Watchdog-Timeout 300 s [F: execution_watchdog.py:8]; Thread-Leak-Thema [F: MC-TC-004-POST-REMEDIATION:558] | asynchrone Verification; Performance-Budget (Phase 5-Tests) [I: B2PKG R3] | offen |
| PR-10 | Rollback-Kosten bei Schema-Revert | **LOW** | [I] Drop = Table-Rebuild [I: §5] | additiv bleiben; Revert nicht als Pfad vorsehen [I] | offen |
| PR-11 | In-Memory-Speicher (Graph `_update_stream` unbegrenzt) | **LOW** | [F] graph.py:54,220-223 | Bound/Prune-Konzept bei Projection-Ausbau [I] | offen |

- [I] Risiko-Profil gesamt: 1 CRITICAL (PR-1), 2 HIGH (PR-2/PR-3), 6 MEDIUM, 2 LOW [I].
- [F] Kein Risiko rechtfertigt ohne Human-Gate eine Entscheidung — Register ist Bewertungsgrundlage [F: HUMAN_DECISION_INDEX].

---

## Validation

- Read-only: keine Datei verändert (außer dieser neuen), kein Commit, keine Implementierung, keine Entscheidung, keine Empfehlung als Fakt.
- Alle [F] mit Datei:Zeile bzw. Artefakt-Referenz; [H]-Aussagen (Genesis-Hash, Snapshot-Intervalle, Rollback-Wege) als Analyse-Spielraum gekennzeichnet, kein Beschluss.
- Konsistent mit MCLS/CLIC/CLAR/ESIA/B2MA, SESSION_RULES v2.0, DECISION_REGISTRY, PROJECT_STATE; Statuslage unverändert.

**Ende nach Erstellung** — keine weiteren Aktionen.
