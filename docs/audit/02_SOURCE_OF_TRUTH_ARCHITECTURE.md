# 02_SOURCE_OF_TRUTH_ARCHITECTURE.md

**Doc:** KF-1/02 · **Date:** 2026-08-02 · **Layer:** STRUCTURED KNOWLEDGE
**Sources:** SESSION_RULES.md v2.0 (§Authoritative Documents), SOURCE_OF_TRUTH_MAP.md (MUSCAL-KRA), AUDIT_SCOPE.md §5 (Confidence), KF-Charter §2/§3
**Validation:** Autoritätskette wörtlich aus SESSION_RULES v2.0 [C0]; Konfliktregeln aus SOURCE_OF_TRUTH + G2-D-017-Resolution

---

## 1. Autoritätsmodell

### 1.1 Prioritätskette (SESSION_RULES v2.0, §Authoritative Documents) [C0]

| Prio | Dokument | Pfad |
|------|----------|------|
| 1 | Project State | `docs/PROJECT_STATE.md` |
| 2 | Audit / Certification Status | `docs/audit/MC-TC-*.md` (neueste Wahrheit ab 27.07) |
| 3 | Technical Baseline | `docs/TECHNICAL_BASELINE.md` |
| 4 | ADRs | `spec/ADR-*.md` |
| 5 | Engineering Decisions | `docs/engineering/D-*.md` |
| 6 | Historical ADRs/RFCs | `archive/history/adrs/*`, `archive/history/rfcs/*` |
| 7 | Architecture | `docs/ARCHITECTURE.md` |
| 8 | README | `README.md` |

**Grundregel [C0]:** Historische Dokumente haben KEINE Autorität über Baseline-Dokumente.
**Erweiterung (Charter §2) [C0]:** Foundation-Dokumente (Doc 00–19) stehen zwischen ADRs (4) und Manuals (Referenz); Manuals sind nie Autorität; `docs/history/*` nie.

### 1.2 Konfliktregel (SESSION_RULES v2.0) [C0]

```
MC-TC-Zertifizierung (Prio 2)
  > PROJECT_STATE (Prio 1 — bei Konflikten nachgezogen, D-017-Resolution G2 §G)
  > Technical Baseline (3)
  > ADRs (4)
  > Engineering Decisions (5)
  > Historisches (6)
```

**Regel:** Konflikte werden **dokumentiert**, nicht stillschweigend aufgelöst.
**Beispiel-Konflikt (live) [C1]:** ADR-014 = PROPOSED in PROJECT_STATE (20.07) vs aktualisierte Datei (28.07) — dokumentiert in SOURCE_OF_TRUTH §2.6, ungelöst, CONFLICTING-Klasse.

### 1.3 De-jure vs De-facto (SOURCE_OF_TRUTH_MAP §1, §2) [C0]

| Domäne | De-jure | De-facto (aktuell) | Befund |
|--------|---------|--------------------|--------|
| Architektur | BASELINE (Prio 3) | BASELINE 12.07, ADRs bis 28.07 | ⚠️ BASELINE stale |
| Implementierung | Git + Code | **197 uncommitted** (Census); heute 104 untracked (Bridge) | ⚠️ Git-Gap |
| Projektstatus | PROJECT_STATE | neuester Stand = Chat 31.07 | ❌ Chat hat neueste Wahrheit |
| Historische Entscheidungen | DECISIONS + Journal | Journal endet 13.07 | ⚠️ 2 Wochen fehlen |

## 2. Evidence-Level (AUDIT_SCOPE §5) [C0]

| Level | Name | Definition | Pflicht |
|-------|------|-----------|---------|
| C0 | VERIFIED | direkter Datei-/String-Match | Kernzahlen, Strukturen |
| C1 | HIGH | mehrere Quellen konsistent | Interpretationen |
| C2 | MEDIUM | Einzelquelle, plausibel | Chat-Entscheidungen (D-010…035) |
| C3 | LOW | Einzelquelle, unverifizierbar | Randaussagen |
| C4 | UNVERIFIABLE | keine Quelle | nur mit Warnung |
| HYP | HYPOTHESIS | interpretative Ableitung | nur markiert |

**Regel (KF-Charter §3) [C0]:** Jede Aussage in Foundation-Dokumenten trägt Tag;
untagged = C4.

## 3. Konfliktauflösung

| Stufe | Vorgehen | Beispiel |
|-------|----------|----------|
| 1. Erkennen | Quellen-Abgleich (SOURCE_OF_TRUTH_ARCHITEKTUR-Review bei Doc-Erstellung) | Manual-Zeilenzahlen vs Code (Census §4) |
| 2. Klassifizieren | Konfliktgrad (LOW/MEDIUM/HIGH) + Confidence beider Seiten | D-017 (doc-level RESOLVED, Rest offen) |
| 3. Dokumentieren | CONFLICTING-Status (Charter §4), keine stille Auflösung | ADR-014-Statuskonflikt |
| 4. Eskalieren | höhere Priorität entscheidet (Prio-Kette 1.2); Human/ARB bei Unklarheit | D-017 → G2 §G-Resolution |
| 5. Schließen | Resolution im Registry (Status-Mutation mit Evidence) | D-040/41 (FL-01a, DEFERRED) |

## 4. Aktualisierungsregeln

| Regel | Inhalt | Quelle |
|-------|--------|--------|
| **Sync-Gate** | PROJECT_STATE nach jedem Audit-Meilenstein aktualisieren | SOURCE_OF_TRUTH §4 SO-1 |
| **Git-als-Wahrheit** | Git-History ist technische Wahrheit; uncommitted Arbeit = Risiko | SOURCE_OF_TRUTH §4 SO-2, CHANGE_JOURNAL-Hierarchie |
| **Chat-Migration** | Chat-only-Status in Repo-Dokumente migrieren (SO-3): MC-TC-007-Status 31.07, MUSCAL-2.0-Richtung 25.07 | SOURCE_OF_TRUTH §4 SO-3 |
| **Status-Mutation** | Statusklassen-Wechsel nur mit Evidence (Charter §4) | KF-Charter |
| **Staleness-Monitor** | letzte-Update-Prüfung je Domäne (SO-1-Manifest) | SOURCE_OF_TRUTH §4 |
| **Kein Überschreiben** | Foundation-Docs referenzieren, kopieren nie Primärquellen | KF-Charter §5 |

---

*Erstellt aus SESSION_RULES v2.0 + SOURCE_OF_TRUTH_MAP + AUDIT_SCOPE. Alle Kernregeln wörtlich [C0] belegt; Zukunftskomponenten nicht als implementiert dargestellt.*
