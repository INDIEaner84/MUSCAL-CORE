# DECISION_CLOSURE_PACKAGE — RC-1 bis RC-6

**Gate:** G5 CONDITIONAL GO (Overall 74.8) · **Date:** 2026-08-01
**Modus:** Dokumentation + Entscheidungsunterlagen — **keine Codeänderungen, keine ADR-Akzeptierung**
**Referenz:** G5_FINAL_READINESS_REPORT.md (RC-1…RC-6), PROJECT_STATE.md, FL01A_FLAKINESS_REGISTER.md

---

## RC-1 — P0-1 / P0-2: Entscheidungsstruktur

### P0-1 — Graph-OS-State Rekonstruktion

**Problemdefinition**
GraphState/SphereState sind rein in-memory; nach Restart nicht rekonstruierbar.
MC-TC-007 Phase H: ❌ FAIL (12/14-Kriterien-Gate, 28.07).

**Aktuelle Architektur** ([C0], Evidenz: MC-TC-007_STATUS_ZUSAMMENFASSUNG.md:67, GRAPH_OS_ARCHITECTURE_FREEZE_v1.0.md)
- Graph-Events (NODE_CREATED, EDGE_CREATED …) WERDEN in `stored_events` persistiert.
- **ABER:** es existiert kein Code, der sie zurückliest (Rebuild-Mechanismus fehlt).
- Widerspruch: GRAPH_OS_ARCHITECTURE_FREEZE v1.0 (24.07) behauptet „ALL P0 BLOCKERS RESOLVED" — Reality-Cert (27.–31.07) widerlegt das für den Rebuild-Teil. Dieser Widerspruch ist Teil der Entscheidung.

**Optionen**

| Option | Beschreibung | Klassifikation | Aufwand |
|--------|--------------|----------------|---------|
| A | Rebuild-Service: `stored_events` → GraphState-Rekonstruktion beim Boot (Phase-K-Boot-Matrix integrieren) | **ARCHITECTURE CHANGE** (neues Feature, vermutlich `features/`) | M–L |
| B | Teilbereich: nur Watchdog-Persistenz (P0-2) fixen; Graph-OS-Rebuild explizit DEFERRED mit Risiko-Dokumentation | Teil-Fix + Governance | S–M |
| C | Akzeptieren als Scope-Boundary („Graph-OS ist Sitzungs-State, kein persisted State"); PROJECT_STATE + ADR-Dokument | Governance-Entscheidung | S |

**Auswirkungen**
- A: Restart-sichere Graph-Zustände; erfüllt MC-TC-007 Phase H; berührt MC-TC-004/006-Replay-Pfad (Integrationstest nötig); ~2–4 Wochen-Schätzung (ohne Zeitplan-Bindung).
- B: Watchdog-Verlust behoben; Graph-OS-Risiko bleibt dokumentiert (R1 G5).
- C: Kein Code; Risiko akzeptiert; „Graph-OS-Sitzungsgebundenheit" als Architektur-Leitlinie.

**Risiken**
- A: Rebuild-Code könnte mit Core-Immutabilität kollidieren → `features/`-Plugin-Pfad erforderlich (D-006).
- B: Restart ohne Graph-Zustand → Anwendungsfälle mit persistenter Session unwirksam.
- C: Produktions-Restart verliert Verifikations-Graph (A-001-artige Risiken, s. MC-TC-003F).

**Offene Human Decision (RC-1a):** Welche Option für P0-1? (Empfehlung des Agenten: B als Sofortmaßnahme + A als Roadmap-Item nach MUSCAL-2.0-Entscheidung; C nur bei expliziter Scope-Freigabe.)

### P0-2 — Watchdog-Events nicht persistent

**Problemdefinition**
Watchdog-Erkennungen (Orphans) überleben keinen Restart; MC-TC-007 Phase F: ✅ PASS* mit Stern.

**Aktuelle Architektur** ([C0], Evidenz: MC-TC-007_STATUS_ZUSAMMENFASSUNG.md:71-76)
- `ExecutionWatchdog._force_fail_orphan()` ruft NUR `event_bus.publish()` — kein `EventStore.append()`.
- Datei: `features/monitoring/execution_watchdog.py:96-119`.
- Folge-Finding C03: Watchdog erkennt denselben Orphan mehrfach (fehlende Dedup-Persistenz).

**Optionen**

| Option | Beschreibung | Klassifikation | Aufwand |
|--------|--------------|----------------|---------|
| A | `_force_fail_orphan()` persistiert zusätzlich über `EventStore.append()` (Rückkanal) | ARCHITECTURE CHANGE (Feature-Pfad, `features/monitoring/` ist NICHT CORE) | S |
| B | Dedup-Marker in EventStore (C03-Fix) + Persistenz in einem Schritt | Feature | S–M |
| C | DEFERRED dokumentieren (Watchdog bleibt Session-only) | Governance | S |

**Auswirkungen / Risiken**
- A/B: Watchdog-Historie über Restart; Orphan-Dedup; MC-TC-007 F → voller PASS. Risiko: Event-Doppelpersistenz (Bridge/Replay-Matrizen prüfen, MC-TC-006).
- C: Fehlende Fehler-Historie; wiederholte Alarme (C03 bleibt).

**Offene Human Decision (RC-1b):** Option A/B/C für P0-2 (Empfehlung: B — klein, behebt F-Stern + C03).

---

## RC-2 — HDR-001: Human Decision Brief

**Kontext**
Architecture Council (HDR-001) ist seit 20.07 „READY FOR HUMAN DECISION" (PROJECT_STATE.md:116, D-023). HDR-002 (PMGA), HDR-003 (Master Coding AI), HDR-004 (Requirements) sind blockiert (9 Dependencies). Kein Agenten-Mandat kann diese Entscheidung treffen.

**Optionen für die Entscheidungsträger**

| Option | Beschreibung |
|--------|--------------|
| 1 | **Genehmigen mit Auflagen** — HDR-001 als angenommen erklären; Auflagen: MC-TC-004-Zertifizierungs-Bedingungen erfüllt (ist), HDR-002…004 mit identischer Evidence-Pflicht starten |
| 2 | **Genehmigen ohne Auflagen** — vollständige Freigabe (Hinweis: P0-1/P0-2 sind unabhängig davon offen) |
| 3 | **Ablehnen / zurückweisen** — HDR-001 an Audit-Findings koppeln (z.B. erst nach RC-1-Entscheidung) |
| 4 | **Teilbereich** — nur HDR-002 freigeben; HDR-003/004 weiter blockiert |

**Benötigte Entscheidung (Formulierung)**
„Erklärt das Architecture Council HDR-001 mit welchen Auflagen als angenommen, und welche HDR-002…004 werden anschließend entblockt?"

**Konsequenzen**
- Option 1/2: Governance-Kette entblockt; M2-induzierter Score-Beitrag (HDR-Rest entfällt); 20-Doc-Plan-Voraussetzung (RC-6) näher.
- Option 3: Status quo bleibt; HDR-002…004 bleiben blockiert (M2-Rest, R2 in G5).
- Option 4: Teil-Fortschritt; HDR-003/004-Dependencies offen.
- In jedem Fall: Entscheidung in PROJECT_STATE/REGISTRY protokollieren (D-023-Update).

---

## RC-3 — FL-01a: Global-State-Entscheidungsentwurf

→ **Separate Datei:** `GLOBAL_STATE_ARCHITECTURE_DECISION_DRAFT.md` (ADR-042-Vorschlag, Optionen A–D, Empfehlung A: Test-Fixtures + Dokumentation).
Zusammenfassung: Singletons (`tools.py:9-24`, `tool_runtime.py:37-42`) ohne Reset;
Empfehlung: Fixture-basierter Test-Reset (Test-only) + ADR-042-Dokument; Produktions-Refactoring erst mit MUSCAL 2.0 (ADR-022). **Keine Akzeptierung ohne Human/ARB-Approval.**

---

## RC-4 — ADR-022…025: Readiness-Prüfung

| ADR | Vollständigkeit | Evidence | Open Questions | Acceptance Readiness |
|-----|-----------------|----------|----------------|----------------------|
| ADR-022 (MUSCAL 2.0 Hybrid) | ✅ Context/Decision-PENDING/Migration/Consequences/Compliance/3 OQ | Registry D-010 (C2, chat-only) | Migrationspfad vs ADR-001; Verhältnis ADR-023/024; Turnier-Kriterien | **NOT READY** — Turnier-Primärquelle nicht im Repo; Migrationsbewertung fehlt |
| ADR-023 (Cognitive Kernel) | ✅ vollständig | D-011 (C2, chat-only) | Autorität vs ADR-014; Edge-Scope; Signierung | **NOT READY** — Sicherheitsmodell unzureichend spezifiziert |
| ADR-024 (Agent P1–P5) | ✅ vollständig | D-012 (C2, chat-only) | P1–P5-Autorisierung; vs ADR-001; Observability-Kriterien | **NOT READY** — P5-Kollision mit Trust-Governance-NO-GO offen |
| ADR-025 (Compiler + RFC) | ✅ vollständig | D-013/D-014 (C2, chat-only) | vs ADR-001-Pipeline; RFC-Governance; D-014-Abgrenzung | **NOT READY** — RFC-Prozess nicht definiert |

**Befund:** Alle 4 formal vollständig und evidenz-verlinkt; **keine** reif zur Akzeptierung
(Chat-Evidenz C2, offene Design-Fragen, Human-Approval-Pflicht). Empfehlung: als
PROPOSED/DRAFT führen; ARB-Review-Runde als RC-4a ansetzen (Review-Ergebnis →
Status-Update, KEINE Auto-Akzeptierung).

---

## RC-5 — M4-Restpunkte: Statusliste

| Item | Status (2026-08-01) | Klassifikation | Nächste Aktion |
|------|---------------------|----------------|----------------|
| D-033 Closed-Source (Plugins only) | PLANNED, chat-only (Registry §C) | Strategy | Plan-Dokument in `docs/governance/` (Phase C, DOC) |
| D-034 Benchmark (vs LangChain/AutoGen/CrewAI) | PLANNED, chat-only | Evaluation | Plan-Dokument (Phase C, DOC) |
| D-035 SLM-Datenstrategie | PLANNED, chat-only | Strategy | Plan-Dokument (Phase C, DOC) |
| v0.8-Manual | **fehlt** (CHANGELOG_v0.8 existiert; kein v0.8-Manual) | DOC | Generierung aus Census/Reconciliation-Daten (Phase C, DOC; TC-H3-Basis) |
| F-03 `specs/adrs/IMPLEMENTATION_STATUS.md` | verwaister Ordner (Inhalt ungeprüft) | DOC | Inhalt prüfen → nach `docs/engineering/`-Schema referenzieren oder als Referenz markieren (keine Löschung) |
| TC-H3 Supersession-Hinweise | PARTIAL (Rangfolge definiert in TECHNICAL_MANUAL_AUTHORITY_MAP; Header-Hinweise fehlen) | DOC | Header-Zeilen in den 3 Manuals (Phase C; Inhaltsänderung — außerhalb dieses Mandats) |

**M4-Effekt:** Erledigung schätzt M4 62 → 70–75 (Hauptgewinne: v0.8 + D-033…035-Docs).

---

## RC-6 — Finale Gate-Checkliste (Voraussetzungen für GO)

| Metrik | Ziel | Messpunkt | Verantwortlich | Status |
|--------|------|-----------|----------------|--------|
| M1 Repository Health | **>75** | Git-State, untracked (Bridge-Governance), Suite-Stabilität | Governance-Team | ✅ 78 (konstant) |
| M2 Governance Consistency | **>75** | ADR-INDEX konsistent, HDR-001 entschieden, MC-TC-005-Klärung | ARB/Human | ✅ 78 (HDR-001-Rest: nach RC-2) |
| M3 Session Continuity | **>75** | Handover 17/17, Checklist v2.0, Stale-Docs (BASELINE/ARCHITECTURE) | Doku-Team | ✅ 78 (Stale-Update optional) |
| M4 Decision Completeness | **>75** | RC-1 (P0-Entscheidung), RC-4 (ADR-022…025-Status), RC-5 (D-033…035, v0.8, F-03, TC-H3) | ARB/Human + Doku | ❌ 62 — Kern der Restarbeit |
| M5 Knowledge Coverage | **>75** | ADR-022…025 gespiegelt (✅), D-033…035-Docs (RC-5) | Doku-Team | ✅ 78 (Rest nach RC-5) |
| **Overall** | **>75** | unweighted avg aller 5 | Measurement-Gate | 74.8 → Ziel nach RC-1/RC-2 |

**GO-Trigger (Reihenfolge):**
1. RC-1a/1b: P0-1/P0-2-Entscheidung (ARB/Human) — M4-K3-Hebel
2. RC-2: HDR-001-Entscheidung (Human) — M2/M4-Rest
3. RC-4a: ADR-022…025-ARB-Review (Status-Klärung, keine Auto-Akzeptierung) — M4-K2
4. RC-5: D-033…035-Docs + v0.8 + F-03 + TC-H3 (DOC) — M4/M5
5. **Re-Messung** (formel-konsistent zu Audit/G2/G4/G5) → alle 5 >75 → **GO: 20-Doc Knowledge Foundation starten** (MASTER_INDEX-Phase-C-Gate)

**Prognose nach Erfüllung:** M1 78 · M2 80 · M3 78 · M4 ~72–75 · M5 80 → **Overall ~77–78 → GO erreichbar.**

---

*Paket erstellt im Decision-Closure-Mandat (RC-1…RC-6). Keine Implementierung; keine ADR-Akzeptierung ohne Human Approval. Stopp nach diesem Paket.*
