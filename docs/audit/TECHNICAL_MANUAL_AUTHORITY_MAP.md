# TECHNICAL_MANUAL_AUTHORITY_MAP — v0.5 / v0.6 / v0.7

**Phase:** G4.5 · **Block:** B3 · **Date:** 2026-08-01
**Modus:** READ-ONLY zu allen Manual-Dateien — **kein Inhalt wurde überschrieben oder verändert**; diese Datei ordnet nur Autoritätsbereiche zu.
**Basis:** TECHNICAL_MANUAL_CONFLICT_REPORT.md (3-Way Reconciliation, Audit) + Sektions-Inventar der drei Manuals (2026-08-01).

---

## Die drei Manuals (unverändert)

| Kürzel | Datei | Version | Sprache | Zeilen | Datum | Umfang |
|--------|-------|---------|---------|--------|-------|--------|
| M-ROOT | `Codebase/TECHNICAL_MANUAL.md` | v0.5 | Englisch | 932 | 2026-07-02 | zwei Codebasen (`muscal/` + `MUSCAL CORE/`) |
| M-0.6 | `MUSCAL CORE/docs/history/technical_manual_v0.6.md` | v0.6 | Deutsch | 1.935 | 2026-07-12 | vollständiges Handbuch (137 Sektionen lt. Conflict Report) |
| M-0.7 | `MUSCAL CORE/TECHNICAL_MANUAL_v0.7.md` | v0.7 | Deutsch | 371 | 2026-07-15 | abridged Stabilisierungs-Handbuch (28 Sektionen) |

---

## Autoritätsbereiche (Zuordnung)

| # | Domäne | Autoritatives Manual | Begründung (Evidence) |
|---|--------|----------------------|------------------------|
| A1 | `muscal/`-Legacy-Paket (Tool-Funktionen, backend/, GraphOptimizer, api_server) | **M-ROOT (v0.5)** | einziges Manual, das `muscal/` beschreibt (TC-M1 [C0]) |
| A2 | CORE-Architektur (7 Schichten, Kernmodule) | **M-0.6** | vollständige Sektionen §2/§4; M-0.7 ist nur Excerpt |
| A3 | Datenmodell / API-Referenz / Konfiguration / Erweiterungspunkte / Einstiegspunkte | **M-0.6** | Sektionen §5/§6/§8/§11/§12 existieren NUR in M-0.6 |
| A4 | System Spine & Layer Governance / MAS-RFC / Capability / MPIR+MREIL / SEL / MAS-VM / Production / Observability | **M-0.6** | Sektionen §14–§21 existieren NUR in M-0.6 |
| A5 | Stabilisierung (v0.6→v0.7: Import-Chain, Pruning, Stress-Test) | **M-0.7** | Sektion §3 „STABILISIERUNG (NEU in v0.7)" NUR in M-0.7 |
| A6 | Abhängigkeiten (v0.7-Übersicht) + Ressourcengrenzen-Übersicht | **M-0.7** | Sektionen §5/§7 „NEU in v0.7"; M-0.6 führt §9-Abhängigkeiten detailreicher |
| A7 | Changelog v0.6→v0.7 | **M-0.7** | Sektion §9 |
| A8 | **Zahlen**: Dateien / LOC / Tests / Stubs | **KEINES** | alle drei unterzählen oder widersprechen sich (TC-H1 [C0], TC-C2 [C0]); verbindlich: REPOSITORY_CENSUS (1.209 Dateien, 611 Python, 77.376 LOC, 204 Test-Dateien, 2.869 Testfunktionen) |
| A9 | **Projektstatus** (Alpha/Beta/Stable/Ready) | **KEINES** | 4 Statuswörter ohne Mapping (TC-M2 [C1]); verbindlich: PROJECT_STATE + MC-TC-Zertifikate |
| A10 | Integrationskarte Cross-Projekt (IPC-Übernahme-Anleitung) | **M-0.6** | Sektion §7 (referenzielle Anleitung) |

---

## Rangfolge bei Mehrfach-Abdeckung

```
Code/Artefakte > Audit-Zertifikate (MC-TC-*) > PROJECT_STATE > ADRs > M-0.6 (vollständig)
  > M-0.7 (abridged, nur Bereiche A5–A7) > M-ROOT (nur Bereiche A1) > docs/history/* (keine Autorität)
```

**Regel (konsistent zu SESSION_RULES v2.0):** Manuals sind Referenz-Dokumente.
Keine Manual-Aussage darf gegen Code, PROJECT_STATE oder Zertifikate zitiert werden
(Conflict-Report-Empfehlung übernommen: „no manual claim should be cited as authoritative").

---

## Verifikation

- Keine der drei Manual-Dateien wurde modifiziert (git status: unverändert).
- Alle Zeilen-/Sektionsangaben stammen aus Dateisystem-Inventar (2026-08-01).
- Diese Map ist die Grundlage für MANUAL_RECONCILIATION_FINAL.md (B4).
