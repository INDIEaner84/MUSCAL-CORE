# KNOWLEDGE_FOUNDATION_CHARTER — 20-Dokumente-Plan

**Gate:** KF-00 · **Date:** 2026-08-01 · **Modus:** Struktur & Mapping (keine Inhalte)
**Referenz:** MASTER_INDEX.md §4 (Phase C), KNOWLEDGE_FOUNDATION_MAPPING.md (PB-05), KNOWLEDGE_FOUNDATION_GATE.md (G7-04)
**Status:** CHARTER — verbindlich für alle 20 Foundation-Dokumente

---

## 1. Zweck der Foundation

Die Knowledge Foundation ist die **kanonische Wissensordnung** des MUSCAL-CORE-
Programms. Sie

1. bündelt das Audit-/Reconciliation-Wissen (17 Audit-Artefakte + In-Repo-Zertifikate) in 20 strukturierte, referenzierbare Dokumente,
2. macht jede Aussage über den Projektzustand auffindbar, mit Quelle und Confidence-Level,
3. ist die Entscheidungsbasis für MUSCAL 2.0 (ADR-022…025) und weitere Gates,
4. ersetzt KEINE Primärquellen — sie referenziert (keine Duplikation).

## 2. Autoritätsmodell (Rangfolge)

```
1. Code / Test-Artefakte (Quelle der Wahrheit für IST-Zustand)
2. Zertifikate (MC-TC-002…007) & Gate-Reports (G2…G7)
3. PROJECT_STATE.md
4. ADRs (spec/ADR-INDEX.md, kanonisch)
5. KNOWLEDGE_FOUNDATION-Dokumente (dieser Plan)
6. Technical Manuals (nur v0.8 nach Freigabe; v0.5–0.7: Referenz, nie Autorität)
7. docs/history/* (keine Autorität)
```

**Regel:** Ein Foundation-Dokument darf nie eine Aussage autorisieren, die gegen
eine höhere Ebene verstößt. Konflikte zwischen Foundation-Dokumenten sind als
CONFLICTING zu markieren, nicht still aufzulösen.

## 3. Evidence-Level (Confidence, aus AUDIT_SCOPE §5)

| Level | Bedeutung | Verwendung |
|-------|-----------|------------|
| **C0** | VERIFIED — direkt durch Dateiinhalt/exakten Match belegt | Kernaussagen, Zahlen, Strukturen |
| **C1** | HIGH — mehrere Quellen stimmen überein | Interpretationen, Querverbindungen |
| **C2** | MEDIUM — einzelne Quelle, plausibel | Chat-/Registry-Entscheidungen |
| **C3** | LOW — einzelne, unverifizierbare oder teils widersprechende Quelle | Randaussagen |
| **C4** | UNVERIFIABLE — keine Quelle, evtl. spekulativ | nur mit Warnhinweis |
| **HYP** | HYPOTHESIS — interpretative Ableitung, Validierung nötig | ausschließlich markiert |

**Pflicht:** Jede Aussage in Foundation-Dokumenten trägt eine Confidence-Tag.
Aussagen ohne Tag gelten als C4 und werden bei Review beanstandet.

## 4. Statusklassen (verbindlich für Entscheidungs- und System-Status)

| Klasse | Definition | Beispiel |
|--------|-----------|----------|
| **IMPLEMENTED** | im Code vorhanden und nachweisbar (C0) | EventStore, Trust Core (MC-TC-004 CERTIFIED) |
| **DOCUMENTED** | als Entscheidung/Stand dokumentiert, ohne Code (C1/C2) | ADR-014 ACCEPTED, D-017 |
| **PLANNED** | geplant/gewollt, keine Umsetzung, kein Beschluss | D-030 E3.6, D-033…035 |
| **CHAT_ONLY** | ausschließlich aus Chat (S2) bekannt, kein Repo-Äquivalent (C2) | D-010…014 (vor ADR-Spiegelung) |
| **HISTORICAL** | historischer Stand, keine aktuelle Gültigkeit | Manuals v0.5–0.7, ADR-013 |
| **CONFLICTING** | widersprechende Quellen, Klärung offen | D-017 (doc-level RESOLVED, Rest offen) |

**Regel:** Statusklassen sind MUTATIONSPFLICHTIG — Wechsel nur mit Evidence
(z.B. CHAT_ONLY → DOCUMENTED erst nach Repo-Spiegelung; PLANNED → IMPLEMENTED
nur mit Code-Beleg C0).

## 5. Dokument-Pflichten

| Pflicht | Inhalt |
|---------|--------|
| Header | Doc-Nummer, Ziel, Quellen, Confidence-Regeln, letzte Validierung |
| Quellen-Binding | Referenz auf FOUNDATION_SOURCE_BINDING.md |
| Kein Volltext-Duplikat | Primärquellen verlinken, nicht kopieren |
| Kein Status-Überverkauf | Statusklassen §4 strikt anwenden |

---

*Charter erstellt — Struktur, kein Inhalt. Referenz für KF-01…KF-03.*
