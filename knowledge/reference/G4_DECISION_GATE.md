# G4_DECISION_GATE — Mission-Control Readiness Gate

**Audit-ID:** MUSCAL-KRA-2026-08-01 · **Date:** 2026-08-01
**Referenz:** G4_MEASUREMENT_REPORT.md (Messbasis, Overall 68.6/100)
**Baseline:** 45.2 → 61.0 → **68.6** (+7.6 seit G2, +23.4 seit Audit)
**Modus:** READ-ONLY-Bewertung — Entscheidung ohne Ausführung

---

## Messergebnis (Zusammenfassung)

| Metrik | Score | >75? |
|--------|-------|------|
| M1 Repository Health | 78 | ✅ |
| M2 Governance Consistency | 72 | ❌ |
| M3 Session Continuity | 78 | ✅ |
| M4 Documentation Redundancy | 50 | ❌ |
| M5 Knowledge Coverage | 65 | ❌ |
| **Overall** | **68.6** | ❌ (−6.4) |

**Besondere Prüfungen:**
1. P0-1/P0-2: **OFFEN** — Entscheidung ausstehend (Blocker)
2. HDR-001: **READY FOR HUMAN DECISION** — blockiert HDR-002…004 (Blocker)
3. ADR_INDEX vs ADR_CANONICAL_MAP: **INKONSISTENT** (F-01 PROPOSED vs ACCEPTED; F-02 5 ADRs fehlen) — DOC-only behebbar
4. SESSION_RULES v2.0: **WIRKSAM** (Checklist, Kette, Forbidden Assumptions; Rerun-Bestätigung offen)
5. D-010…D-035: **VOLLSTÄNDIG KONSOLIDIERT** (21/21, 0 CONFLICTING)

---

## Entscheidung: B — CONDITIONAL GO

**Begründung:**
- **Kein A (GO):** Overall 68.6 < 75; M2/M4/M5 unter Ziel; Phase-C-Definition (MASTER_INDEX: „target >75 on all 5; only then start the 20-document plan") nicht erfüllt.
- **Kein C (NO-GO):** Keine Governance-Defekte — Mechanismen funktionieren (Override aktiv, Suite stabil, Handover 100%, Registry konsolidiert). Die verbleibenden Lücken sind **bewusste, dokumentierte Folge-Items** (F-01…F-03, TF-02/TF-06, chat-only-ADRs) und **Entscheidungs-Blocker** — keine Reparatur-Aufgaben. Phase A/B haben die Arbeitsbasis vollständig geliefert.

**G4-Verdict: CONDITIONAL GO — 20-Doc-Plan nach Erfüllung der Bedingungen B1–B5 (bzw. B4/B5 durch Entscheidung) startbar.**

---

## Konkrete Blocker (Bedingungen)

### DOC-only-Items (Governance-Artefakte, kein Code) — erledigen vor 20-Doc-Plan-Start

| ID | Blocker | Metrik-Hebel | Evidence/Referenz | Aufwand |
|----|---------|--------------|-------------------|---------|
| **B1** | ADR-INDEX aktualisieren: ADR-014 → ACCEPTED (01.08); ADR-013-Supersession-Zeile konsistent | M2 → 77 | ADR_CANONICAL_MAP.md F-01 | S |
| **B2** | 5 ADRs in INDEX aufnehmen: ADR-API-001, ADR-EVENT-001, ADR-RUNTIME-001, ADR-020, ADR-021 | M2 → 77 | ADR_CANONICAL_MAP.md F-02 | S |
| **B3** | ADR-022…025-Entwürfe (PENDING) aus D-010…D-014 + D-033…D-035-Plan-Dokumente | M5 → 75 | DECISION_REGISTRY, G3-Plan §3.4 | M |
| **B4** | Manuals-Triple konsolidieren (TF-02/TF-06) + specs/adrs/-Leiche auflösen (F-03) | M4 → ~70 | G3-Plan §5 R4, MASTER_INDEX M4 | M (größter M4-Hebel; verbleibender Rest ~5 Punkte) |

### Entscheidungs-Blocker (außerhalb DOC-Mandat — erfordern ARB/Human)

| ID | Blocker | Status | Erforderliche Aktion |
|----|---------|--------|----------------------|
| **B5** | P0-1 (Graph-OS Reconstruction) / P0-2 (Watchdog-Persistenz) | OFFEN (PA-08/PA-09) | Option wählen oder als ARCHITECTURE CHANGE deklarieren (ARB/OVERRIDE-Pfad) |
| **B6** | HDR-001 Human Decision | READY FOR HUMAN DECISION (D-023) | Menschliche Entscheidung; entblockt HDR-002…004 |
| **B7** | FL-01a-Fix-Entscheidung (D-040/D-042) | Deferred | Fix (Test-Fixtures) oder dauerhafte Dokumentation beschließen |

---

## Startbedingung 20-Doc-Plan

```
GO-THROTTLE:
  1. B1 + B2 erledigt                    (M2 ≥ 77)
  2. B3 erledigt                         (M5 ≥ 75)
  3. B4 erledigt                         (M4 ≥ 70, Restlücke dokumentiert)
  4. B5 + B6 entschieden                 (P0-Entscheidung + HDR-001)
  5. Re-Messung bestätigt Overall >75
DANN: 20-Doc-Plan mit KNOWLEDGE_FOUNDATION_MAPPING.md (PB-05) als Arbeitsvorlage.
```

**Reihenfolge-Empfehlung:** B1→B2 (S) → B3 (M) parallel zu B5/B6 (Entscheidungen) → B4 (M) → Re-Messung.

---

## Verantwortlichkeiten

| Item | Zuständig |
|------|-----------|
| B1–B4 (DOC-only) | Governance/Konsolidierungs-Agent (nächstes Mandat) |
| B5, B7 | ARB / Architecture Review Board |
| B6 | Human (Projektleitung) |
| Re-Messung | Measurement-Gate-Agent (Formel-konsistent zu MASTER_INDEX/G2/G4) |

---

## Ausblick ohne Bedingungen

Ohne B5/B6 bleibt das Projekt **CONDITIONAL** (Qualitätspfad fertiggestellt, Entscheidungs-Gate offen): Governance, Continuity und Knowledge-Basis sind vorbereitet — der formale Mission-Control-Status (>75) wird erst nach den Entscheidungen erreicht.

---

*G4-Bewertung abgeschlossen (READ-ONLY). Keine Codeänderung, keine Migration, keine neuen Dokumentstrukturen außerhalb `KNOWLEDGE_FOUNDATION/audit/`. Stopp nach G4.*
