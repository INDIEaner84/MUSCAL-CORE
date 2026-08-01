# TC_H3_CLOSURE — Manual-Version-Hierarchie: Entscheidungsmatrix

**Gate:** G6-03 · **Date:** 2026-08-01 · **Modus:** READ/WRITE (docs/audit/)
**Referenz:** MANUAL_RECONCILIATION_FINAL.md (TC-H3: PARTIAL), TECHNICAL_MANUAL_AUTHORITY_MAP.md, G6-02 (v0.8-Scope)
**Problem:** TC-H3 [C1] — keine Manual-Datei deklariert „dies ersetzt X"; Version-Hierarchie war undefiniert.

---

## Entscheidungsmatrix (2026-08-01)

| # | Konflikt-Aspekt | Status | Entscheidung / Stand | Evidence |
|---|-----------------|--------|----------------------|----------|
| 1 | **Autoritäts-Rangfolge** (welche Quelle gewinnt bei Widerspruch) | ✅ **RESOLVED** | Rangfolge: Code > Zertifikate > PROJECT_STATE > ADRs > v0.8 (künftig) > M-0.6 > M-0.7 > M-ROOT > history (A8/A9); Manuals sind Referenz, nie Autorität | TECHNICAL_MANUAL_AUTHORITY_MAP.md (2026-08-01) |
| 2 | **Zahlen-Autorität** (Dateien/LOC/Tests/Stubs) | ✅ **RESOLVED** | Census/Reconciliation als einzige zitierfähige Quelle; Alt-Manual-Zahlen verworfen (TC-H1/TC-C2) | MANUAL_RECONCILIATION_FINAL §1, G6-02 §1 |
| 3 | **Status-Vokabular** (Alpha/Beta/Stable/Ready) | ✅ **RESOLVED** | Status-Mapping: PROJECT_STATE + MC-TC-Zertifikate verbindlich; Manual-Statuswörter historisch | MANUAL_RECONCILIATION_FINAL §2 |
| 4 | **Explizite Supersession-Hinweise in M-ROOT/M-0.6/M-0.7** (Header „superseded by v0.8") | ⚠️ **PARTIAL** | Rangfolge + Zielzustand definiert; Header-Zeilen existieren NICHT (Inhaltsänderung an Alt-Manuals — in G6-Mandat verboten, „Keine Migration") | G6-02 §4, MANUAL_RECONCILIATION_FINAL §3-2 |
| 5 | **v0.8-Erzeugung** (kanonisches Handbuch) | ⚠️ **PARTIAL** | Scope-Dokument fertig (G6-02); **Datei `TECHNICAL_MANUAL_v0.8.md` existiert noch nicht** — Erzeugung = Phase-C-DOC-Item nach Scope-Freigabe | TECHNICAL_MANUAL_v0.8_SCOPE.md |
| 6 | **Alt-Manual-Archivierung** (docs/history/-Zuordnung, keine Löschung) | ⚠️ **OPEN** | Zielzustand definiert (v0.8-Freigabe → Archivierung); durchgeführt erst nach v0.8-Freigabe | G6-02 §6 |
| 7 | **requirements-Autorität** (txt vs lock vs spec.yaml, TC-L1) | ⚠️ **OPEN** | unabhängig von TC-H3; Paket-Governance-Konzept (Phase C) | MANUAL_RECONCILIATION_FINAL §3-3 |
| 8 | **Untracked-Reports** (E3.1-PHASE2, E3.3-LEDGER, TC-L2) | ⚠️ **OPEN** | Commit als Phase-C-Dokumentations-Item empfohlen | MANUAL_RECONCILIATION_FINAL §3-4 |

## Ergebnis

- **RESOLVED: 3/8** (Kern des TC-H3: Autoritäts- und Zahlen-Fragen gelöst)
- **PARTIAL: 2/8** (Header-Hinweise + v0.8 — beide an Phase-C-Freigabe gekoppelt)
- **OPEN: 3/8** (Archivierung, TC-L1, TC-L2 — nachgelagert, ohne Readiness-Wirkung)

## Wirkung auf M4

TC-H3-Kern (Rangfolge/Zahlen) ist RESOLVED → Redundanz-Komponente stabil.
Verbleibender M4-Hebel: v0.8-Erzeugung (Phase C), nicht durch dieses Artefakt.

---

*G6-03 abgeschlossen — Dokumentation + Matrix; keine Alt-Manual-Datei verändert.*
