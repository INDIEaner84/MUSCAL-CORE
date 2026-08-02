# ADR_REVIEW_PACKET — RC-4a Review-Unterlage (ADR-022…025)

- Datum: 02.08.2026
- Zweck: Review-Packet für die ARB-Review-Runde RC-4a (read-only; **keine Akzeptanzannahme**, keine Statusänderung, keine Bewertung — nur Aufbereitung vorhandener Evidenz)
- Basis: spec/ADR-022…025, DECISION_CLOSURE_PACKAGE §RC-4, ADR_REVIEW_MATRIX.md (G7-03), G6_01_ADR_CLOSURE_PREPARATION.md, 05_DECISION_REGISTRY_FOUNDATION (D-010…D-014), MC-TC-007-TRUST-GOVERNANCE-CERTIFICATION.md, MC-TC-007-FULL-REALITY-CLOSURE-CERTIFICATION.md
- Status: **created, not committed (external KF layer)**
- Hinweis: Alle 4 ADRs bleiben **PROPOSED (DRAFT)** — keine automatische Akzeptierung (G4.5-B2; ADR_REVIEW_MATRIX; DECISION_CLOSURE_PACKAGE §RC-4).

---

## Übersicht

| ADR | Titel | Quelle (Registry) | Evidence | Status | Review-Status (G7-03) |
|-----|-------|-------------------|----------|--------|------------------------|
| ADR-022 | MUSCAL 2.0 Hybrid-Architektur (MC-015) | D-010 (25.07, chat-only, C2) | C2 (Chat) | PROPOSED (DRAFT) | NICHT GESTARTET |
| ADR-023 | Cognitive Kernel + Authoritative Runtime (Edge) | D-011 (25.07, chat-only, C2) | C2 (Chat) | PROPOSED (DRAFT) | NICHT GESTARTET |
| ADR-024 | Agent-Architektur-Prinzipien P1–P5 | D-012 (30.07, chat-only, C2) | C2 (Chat) | PROPOSED (DRAFT) | NICHT GESTARTET |
| ADR-025 | Cognitive Compiler — Prompts als deklarative kognitive Programme | D-013 (30.07) + D-014 (29.07), chat-only, C2 | C2 (Chat) | PROPOSED (DRAFT) | NICHT GESTARTET |

Alle: formal vollständig (6/6, G6-01), evidenz-verlinkt, aber **NOT READY** (DECISION_CLOSURE_PACKAGE §RC-4) — keine reif zur Akzeptierung.

---

## ADR-022 — MUSCAL 2.0 Hybrid-Architektur

### Zweck
Dokumentiert den Stand des MC-015-Architektur-Turniers (25.07, Chat): Hybrid-Architektur aus durable execution + hierarchischem Multi-Agenten-Modell + event-driven verification; Alternative: Fortführung des Single-Agent-Kernels (D-001-Pfad, ADR-001 APPLIED).

### Quelle
DECISION_REGISTRY D-010 (S2 `MUSCAL 2.0 Architektur-Turnier`, 25.07, chat-only); spec/ADR-022-muscal2-hybrid.md (01.08, PROPOSED); G4.5 Consolidation Agent (B2).

### Evidence-Level
C2 (Chat-only, D-010); kein Repo-Artefakt des Turniers („Entscheidung existiert nur im Chat"; ADR-022 Context).

### Aktueller Status
PROPOSED (DRAFT) — PENDING, keine Entscheidung getroffen; Migrationspfad unbestimmt; ADR-022-Abhängigkeit bei RC-1-Option D (G7-01).

### Offene Review-Fragen
1. Migrationspfad von ADR-001 (Single-Pipeline) zu Hybrid — wer entscheidet? (ADR-022 OQ-1)
2. Verhältnis zu ADR-024 (Agent-Prinzipien) und ADR-023 (Cognitive Kernel)? (OQ-2)
3. Turnier-Treffer-Kriterien dokumentieren (Quelle S2-Chat 25.07, nicht im Repo) (OQ-3)
4. G6-01-Kategorien fehlend: Akzeptanzkriterien, Owner, Zeitplan, Budget, Rückwärtskompatibilität, Review-Prozess (ADR_REVIEW_MATRIX)
5. Konflikt D-010 vs D-001 (Migrationspfad, MEDIUM) — Kernfrage: Migrationspfad oder Koexistenz (ADR_REVIEW_MATRIX)

### Abhängigkeiten
ADR-001 (Kernel), ADR-005 (Pipeline), ADR-006 (Graph), D-030 (E3.6-Roadmap) (ADR_REVIEW_MATRIX); RC-1-Option-D-Bezug (G7-01); Migrationsbewertung/ADR-001-Bezug fehlt (KF3-Queue §RC-4a).

### Benötigte ARB-Aktion
- Turnier-Primärquelle (MC-015-Chat 25.07) beschaffen/importieren oder Beschaffbarkeit klären (NOT READY-Grund, §RC-4; KF3-L-9)
- Migrationsbewertung ADR-001→Hybrid ergänzen
- Datei-OQs (3) beantworten + G6-01-Kategorien als Template-Anforderungen annehmen (ADR_REVIEW_MATRIX Review-Protokoll 1)
- Konflikt-Urteil D-010 vs D-001 (MEDIUM): bestätigen/verwerfen/ergänzen (Protokoll 2)
- Ergebnis → Status-Empfehlung (PROPOSED-final/DEPRECATED/ACCEPTED) — Entscheidung durch ARB/Human, nicht durch diesen Agenten (Protokoll 3)

---

## ADR-023 — Cognitive Kernel + Authoritative Runtime (Edge)

### Zweck
Dokumentiert den Cognitive-Kernel-Vorschlag (25.07, Chat): Authoritative Runtime auf Edge-Hardware, signed actions, verifizierter Event Store (anschlussfähig an MC-TC-004/006-Zertifizierungen).

### Quelle
DECISION_REGISTRY D-011 (S2 `Cognitive Kernel Proposal`, 25.07, chat-only); spec/ADR-023-cognitive-kernel.md (01.08, PROPOSED).

### Evidence-Level
C2 (Chat-only, D-011); kein Repo-Artefakt.

### Aktueller Status
PROPOSED (DRAFT) — PENDING; **NOT READY: Sicherheitsmodell unzureichend spezifiziert** (DECISION_CLOSURE_PACKAGE §RC-4; KF3-M-4).

### Offene Review-Fragen (Fokus Security Model)
1. Autorität im Verhältnis zu ADR-014 (UToolRuntime) und Trust-Governance-NO-GO? (ADR-023 OQ-1)
2. Edge-Scope: welche Laufzeit-Umgebung (vgl. ADR-008 Deployment)? (OQ-2)
3. Signierungs-Schema und Schlüsselverwaltung — Design offen (OQ-3)
4. Sicherheitsmodell: Wie verhält sich der Anspruch „signed actions" zur festgestellten Governance-Lage? (KF3-M-4)
5. G6-01-Kategorien fehlend: Akzeptanzkriterien, Owner, Zeitplan, Budget, Rückwärtskompatibilität, Review-Prozess (ADR_REVIEW_MATRIX)

### Konflikt-Bezug (Security Model ↔ Trust Governance)
- MC-TC-007-TRUST-GOVERNANCE-CERTIFICATION: **NO-GO ❌** — Governance ↔ EventStore-Disconnect: alle 5 `emit_tool_*`- und 5 `emit_interface_*`-Events (RuntimeObservability) haben **ZERO Caller**; ApprovalManager mit Auto-Approve ohne Human (features/tools/approval.py:10); Governance-Persistenz = None (nur in-memory).
- ADR-023 Consequences: „Offen: Hardware-Anforderungen, Sicherheitsmodell, Verhältnis zu MC-TC-007-Trust-Governance-Findings (NO-GO: Governance nicht persistent)".
- ADR_REVIEW_MATRIX-Konflikt: ADR-023 vs Trust-Governance-NO-GO = **MEDIUM** (Cognitive-Kernel-Anspruch „signed actions" kollidiert mit fehlender Governance-Persistenz).

### Abhängigkeiten
ADR-014 (Unified Tool Runtime), ADR-008 (Deployment/Edge), ADR-EVENT-001 (EventStore Boundary) (ADR-023 Migration Plan; ADR_REVIEW_MATRIX).

### Benötigte ARB-Aktion
- Sicherheitsmodell spezifizieren lassen: Signierungs-Schema, Schlüsselverwaltung, Verhältnis zur Governance-Realität (NO-GO, Auto-Approve, ZERO-Caller) — Review-Frage an Ersteller/ARB (KF3-M-4)
- Verhältnis ADR-014 + ADR-EVENT-001 klären (OQ-1)
- Edge-Scope (ADR-008-Bezug) festlegen (OQ-2)
- Datei-OQs + G6-01-Kategorien beantworten; Konflikt-Urteil NO-GO-Bezug; Status-Empfehlung (Review-Protokoll)

---

## ADR-024 — Agent-Architektur-Prinzipien P1–P5

### Zweck
Dokumentiert die Agent-Architektur-Spezifikation (30.07, Chat, Spec-Draft): fünf Prinzipien P1 Modularity, P2 Specialization, P3 Observability, P4 Replaceability, P5 Human Sovereignty.

### Quelle
DECISION_REGISTRY D-012 (S2 `MUSCAL Agent Architecture`, 30.07, chat-only); spec/ADR-024-agent-architecture.md (01.08, PROPOSED).

### Evidence-Level
C2 (Chat-only, D-012); kein Repo-Artefakt.

### Aktueller Status
PROPOSED (DRAFT) — PENDING; **NOT READY: P5-Kollision mit Trust-Governance-NO-GO offen** (DECISION_CLOSURE_PACKAGE §RC-4; KF3-M-4).

### Offene Review-Fragen (Fokus P5 Collision / Trust Governance)
1. Verbindliche Definition von P1–P5 — wer autorisiert? (ADR-024 OQ-1)
2. Verhältnis zu ADR-001 (Single Pipeline Authority) — ersetzt oder erweitert? (OQ-2)
3. Prüfverfahren für P3 (Observability) — anknüpfend an RuntimeObservability-ZERO-Caller-Finding (MC-TC-007)? (OQ-3)
4. **P5 (Human Sovereignty) vs Auto-Approve-Struktur**: ApprovalManager (features/tools/approval.py:10) = Auto-approve ohne Human; Bypass-Register P0-001 (`mel.py:54`), P0-002 (`permission_engine.py:47`), P0-003 (Kernel) — kein Konflikt im Code, aber Governance-Gap (ADR-024 Consequences; MC-TC-007-TRUST-GOVERNANCE §1/§3)
5. Klarstellung: Gilt P5 für MUSCAL-2.0-Agenten oder auch heute? (ADR_REVIEW_MATRIX Konflikt-Zeile)
6. G6-01-Kategorien fehlend: Akzeptanzkriterien, Owner, Zeitplan, Budget, Rückwärtskompatibilität, Review-Prozess (ADR_REVIEW_MATRIX)

### Abhängigkeiten
ADR-021 (Agent Detection Formalization), ADR-022 (Multi-Agent), ADR-001 (Pipeline), ADR-007 (P5/Authority) (ADR-024 Migration Plan; ADR_REVIEW_MATRIX).

### Benötigte ARB-Aktion
- P5/Trust-Governance-Verhältnis klären: Kollision mit Auto-Approve bewerten; Geltungsbereich (heute vs MUSCAL 2.0) festlegen (ADR_REVIEW_MATRIX; KF3-M-4)
- P3-Observability-Prüfverfahren an ZERO-Caller-Finding anbinden (OQ-3)
- ADR-001-Verhältnis (OQ-2), P1–P5-Autorisierung (OQ-1) beantworten; Status-Empfehlung (Review-Protokoll)

---

## ADR-025 — Cognitive Compiler — Prompts als deklarative kognitive Programme

### Zweck
Dokumentiert zwei verwandte Chat-Entscheidungen: D-013 (30.07): Prompts als deklarative kognitive Programme (Compiler v1.0, implementierungsorientiert); D-014 (29.07): formale Spezifikation als RFC-Serie (implementierungsunabhängig). Abgrenzungsvorschlag (kein Beschluss): D-014 spezifiziert „was", D-013 „wie"; D-014 Vorrang bei Konflikten.

### Quelle
DECISION_REGISTRY D-013 (S2 `MUSCAL Compiler Spezifikation`, 30.07, chat-only) + D-014 (S2 `formale Spezifikation`, 29.07, chat-only); spec/ADR-025-cognitive-compiler.md (01.08, PROPOSED).

### Evidence-Level
C2 (Chat-only, D-013/D-014); kein Repo-Artefakt.

### Aktueller Status
PROPOSED (DRAFT) — PENDING; **NOT READY: RFC-Prozess nicht definiert** (DECISION_CLOSURE_PACKAGE §RC-4; KF3-M-4).

### Offene Review-Fragen (Fokus RFC Process)
1. Ist der Cognitive Compiler eine Erweiterung von ADR-001 oder eine neue Pipeline? (ADR-025 OQ-1)
2. RFC-Serie: Zuständigkeit, Format, Veröffentlichungsprozess? (OQ-2)
3. D-014-Abgrenzung: bestätigen oder verwerfen? (OQ-3)
4. **RFC-Process nicht definiert**: keine Governance für RFC-Nummerierung, Autoritätsstufe, Review-Freigabe (ADR-025 Consequences; KF3-M-4)
5. Konflikt D-013 vs D-014 (LOW, unterschiedliche Scopes) — Review bestätigt oder verfeinert (ADR_REVIEW_MATRIX)
6. G6-01-Kategorien fehlend: Akzeptanzkriterien, Owner, Zeitplan, Budget, Rückwärtskompatibilität, Review-Prozess (ADR_REVIEW_MATRIX)

### Abhängigkeiten
ADR-001 (Compiler-Pipeline im Kernel), MPIR/MREIL (M-0.6 §17, Referenz), ADR-022 (Compiler im Hybrid-Kontext) (ADR-025 Migration Plan; ADR_REVIEW_MATRIX); Eingangsdaten D-012/D-013-Klärung über B5 (KF3-Queue §RC-4a).

### Benötigte ARB-Aktion
- RFC-Prozess definieren (Zuständigkeit, Format, Veröffentlichung, Autoritätsstufe) oder bewusst delegieren (KF3-M-4)
- ADR-001-Verhältnis (OQ-1) und D-013/D-014-Abgrenzung (OQ-3) beantworten
- Datei-OQs + G6-01-Kategorien beantworten; Konflikt-Urteil D-013 vs D-014 (LOW); Status-Empfehlung (Review-Protokoll)

---

## Übergreifende Abhängigkeiten (alle 4 ADRs)

- D-030 (E3.6-Meilenstein) + Trust-Governance-NO-GO (MC-TC-007, 30.07) (ADR_REVIEW_MATRIX Abhängigkeits-Graph)
- Basis D-010…D-014: CHAT_ONLY, C2 — bleibt CHAT_ONLY (G6-04-Regel; 05_DECISION_REGISTRY §F)
- M4-K2-Eingangsgröße: ADR-Status (13/17 akzeptiert, 4 DRAFT 022…025) (G6_READINESS_RECHECK §2)
- Architektur-Dokumente Doc 04/14 (DRAFT-Knoten im REFERENCE_GRAPH) (KF3-Queue §RC-4a)
- Akzeptanz blockiert Folge-Architektur-Dokumente (KF-03) — blockiert Akzeptanz-Bezug, nicht die Dokumente (KF3-L-3-Korrektur)

## Review-Protokoll (für RC-4a, aus ADR_REVIEW_MATRIX)

1. ARB beantwortet je ADR die Datei-OQs (3) + nimmt G6-01-Kategorien als Template-Anforderungen an.
2. Konflikt-Urteile je Zeile (bestätigen / verwerfen / ergänzen).
3. Ergebnis → Status-Empfehlung (PROPOSED-final / DEPRECATED / ACCEPTED) — Entscheidung durch ARB/Human, nicht durch diesen Agenten.
4. Ergebnis-Protokoll in ADR_INDEX + ADR-Dateien (nur durch Review-Instanz).

## Validation

- Read-only: keine Akzeptanzannahme, keine Bewertung, keine Statusänderung, keine Score-Berechnung; alle Aussagen mit Quelle (ADR-Dateien, §RC-4, G7-03-Matrix, MC-TC-007-Artefakte, Registry).
- ADR-Status PROPOSED (DRAFT) unverändert; D-010…D-014 CHAT_ONLY unverändert.
