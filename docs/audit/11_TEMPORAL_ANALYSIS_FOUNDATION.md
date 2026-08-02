# 11_TEMPORAL_ANALYSIS_FOUNDATION.md

**Doc:** KF-1/11 · **Date:** 2026-08-02 · **Layer:** STRUCTURED KNOWLEDGE (konsolidiert)
**Sources:** CONCEPT_EVOLUTION_MAP.md (Concept-Register §1, Stabilität §2, Temporal-Map §3, offene Fragen §4) · DECISION_REGISTRY.md + 05_DECISION_REGISTRY_FOUNDATION (D-001…D-042) · SOURCE_OF_TRUTH_MAP (§2-Altersdaten) · SESSION_CONTINUITY_AUDIT (§4-Freshness) · MANUAL_RECONCILIATION_FINAL (Manual-Zeiten) · G6_READINESS_RECHECK (M4-Metrikwechsel) · G7-03 (ADR-Review-Konflikte)
**Modus:** Read-only Zeitordnung — **Erstauftritte nur mit Beleg, keine neuen Hypothesen, keine Zukunftsprognosen**

---

## 1. Purpose

Dieses Dokument ordnet die Wissens-Evolution des MUSCAL-Programms zeitlich: Konzepte, Entscheidungen, Governance-Mechanismen und Dokumentation mit ihren **belegten Erstauftritten** und Übergängen. Es ist die operative Referenz für die Temporal-Analyse und liefert die Zeitachse für Doc 04 (Knowledge Graph).

## 2. Scope

| In | Out |
|----|-----|
| belegte Erstauftritte/Timelines aus Concept-Evolution-Map + Registry + Audit-Daten | neue Evolutionshypothesen, Prognosen, Interpretationsmodelle über Artefakt-Inhalt hinaus |

**Confidence-Hinweis (belegt):** Concept-Definitionen C0 (dokumentiert) bzw. C2 (chat-abgeleitet); Erstauftritte aus S1-Titeln [C2], S2-Headern [C0], Repo/Commits [C0] (Concept-Map §Provenance).

## 3. Temporal Methodology (bestehend, nicht neu)

| Element | Methode | Beleg |
|---------|---------|-------|
| Concept-Register | Erstauftritt + aktuelle Definition + Evolution je Konzept | CONCEPT_EVOLUTION_MAP §1 |
| Stabilitäts-Einstufung | Stable core / Evolving / Abandoned / Reintroduced | §2 [C0/C1/C2] |
| Wellen-Karte | 8 Zeitfenster 2024-02 → 2026-07-31 mit Wissens-Wellen | §3 |
| Datierungsquellen | S1-Titel (Monatszählung), S2-Header (Datum), git log, mtimes | §Provenance |

## 4. Concept Timeline (Erstauftritte nur mit Beleg)

| Concept | Erstauftritt (belegt) | Aktuelle Definition (Kurz) | Quelle |
|---------|------------------------|----------------------------|--------|
| MUSCAL | 2026-05-27 (S1 „MUSCAL Mode Aktivierung") | Cognitive OS / Sprache / Framework (3 Ansprüche) | Concept-Map §1 [C2/C0] |
| MUSCAL CORE | 2026-06 (ROADMAP v0.1-Meilenstein) | v0.7 „Stable Prototype"; v0.8-Changelog, kein v0.8-Manual | §1 [C0] |
| MREIL / MPP | ≤2026-06-30 (S1 „Architektur Spezifikation"; 16-Stufen-Pipeline) | stabil innerhalb MPP | §1 [C2] |
| ALITA | 2026-07-07 (S1 „ALITA Design Book Konzept") | Desktop-Agent + HUD, Knowledge Architecture Engine | §1 [C2] |
| MCXF | ≤2026-07-07 (S1 „MCXF Spezifikation") | 🗑 abgelöst durch D-001 (04.07), Compiler-Pfad | §1/§2 [C1] |
| EventBus | v0.7-Bounding (D-005, 06.07) | stabil | §1 [C0] |
| EventStore | 2026-07-19/20 (Commits b9b17f3, 763f6bf) | append-only + Replay; MC-TC-004 zertifiziert | §1 [C0] |
| AuditLog | 2026-07-21 (S2) | Konzept-Stadium (semantische Trennung D-008) | §1 [C2] |
| Graph-OS | ≤2026-07-23 (S2 Meta-UI/GUI-Vorlage) | Visualisierungsschicht — **nicht zertifiziert, in-memory**, P0-1 | §1 [C2]; G5-B5 |
| Trust Core | ≤2026-07-23 (E3.2) | minimales Set, MC-TC-003F/004 zertifiziert | §1 [C0/C1] |
| HDR-001…004 | 2026-07-20 (PROJECT_STATE) | HDR-001 offen, blockiert HDR-002…004 (9 Dependencies) | §1 [C1]; G5-B6 |
| MUSCAL 2.0 | 2026-07-25 (S2 Turnier) | Hybrid (MC-015) — ADR-022 DRAFT | §1 [C2]; G7-03 |
| Cognitive Kernel | 2026-07-25 (S2 Proposal) | Edge-Runtime, signed actions — ADR-023 DRAFT | §1 [C2] |
| MUSCAL Agent System | 2026-07-21 (S2) → 30.07 Spec v1.0 | Agent = Rolle, P1–P5 — ADR-024 DRAFT | §1 [C2] |
| Cognitive Compiler | 2026-07-30 (S2 Spec) | Prompts als Programme, Semantic AST/CIR — ADR-025 DRAFT | §1 [C2] |
| KIR | ≤2026-07-07 (S1 „KIR Spezifikation") | Cognitive Memory; Repo-Status unklar (GAP) | §1 [C2] |

## 5. Decision Timeline (D-IDs, Registry-Daten)

| Fenster | Entscheidungen | Beleg |
|---------|----------------|-------|
| 04.–11.07 | D-001…D-007 (Architektur/Stabilisierung/Governance: Compiler, 7-Layer, Capability-First, Plugins, EventStore-Plugin, Bounding) | Registry §A [C0] |
| 12.–13.07 | D-022 (Git-Hierarchie), Journal-Ende 13.07 | Registry §B [C0] |
| 20.–21.07 | D-023 (HDR-001), D-025 (ADR-Autorität), D-008/D-009 (Semantik/Append), D-032 (Agenten-Vision) | §A/§B/§C [C0/C2] |
| 23.–25.07 | D-015 (E3.2-Closure), D-010/D-011 (2.0/Kernel), D-024 (ExecutionMode), D-033 (Closed-Source) | §A/§B/§C [C1/C2] |
| 27.–31.07 | D-030/D-031 (E3.6, Reality-Score), D-014 (RFC), D-012/D-013 (Agent/Compiler), D-016 (MC-TC-004), D-017 (MC-TC-007), D-018 (ADR-014) | §A/§C [C1/C2] |
| 01.08 (G2) | D-036…D-042 (Adjudikation, FL-01a/b, Global-State-ADR) | Registry §F [C0/C1] |

## 6. Governance Timeline

| Datum | Ereignis | Beleg |
|-------|----------|-------|
| 06.07 | D-020 Immutability-Contract (OVERRIDE + `--allow-core-write`) | Registry §B [C0] |
| 11.07 | D-021 Handover-Pflicht | §B [C1] |
| 12.07 | D-022 Autoritäts-Hierarchie (Git → Journal → Registry) | §B [C0] |
| 20.07 | HDR-001 READY FOR HUMAN DECISION (blockiert seitdem) | §B; PROJECT_STATE [C1] |
| 24.07 | OVERRIDE.md-Rewrite (1.298→189 Z.) — OVERRIDE-052 deaktiviert (Defekt) | G2-Report §3 [C0] |
| 27.–30.07 | Audit-Welle MC-TC-002…007 (55 Dateien, untracked) | G2-Report, Census [C0] |
| 01.08 | G2: OVERRIDE rekonstruiert (1.541 Z., OVERRIDE-052 aktiv); SESSION_RULES v2.0 (PB-03) | G2-Execution, G4 [C0] |

## 7. Documentation Timeline (belegte Altersdaten, keine Neuberechnung)

| Dokument | Datum | Befund | Quelle |
|----------|-------|--------|--------|
| TECHNICAL_MANUAL v0.5 (M-ROOT) | 02.07 | älteste Version, Zwei-Codebase-Scope | Conflict-Report §1 [C0] |
| TECHNICAL_MANUAL v0.6 | 12.07 | Voll-Manual, „~45% Stubs" | §1 [C0] |
| TECHNICAL_MANUAL v0.7 | 15.07 | Auszug (28 Sektionen), kopierte Zahlen, TC-C1 | §1 [C0] |
| ROADMAP | 08.07 | stale (24 Tage bei Audit) | SESSION_CONTINUITY §4 [C0] |
| PROJECT_STATE | 20.07 (+P0-Update 01.08) | Basis 20.07, P0-Teil 01.08 | §4; D-017-Resolution [C0] |
| CHANGE_JOURNAL | 13.07 | endet C-004 | Census §7 [C0] |
| docs/audit/ | 23.–30.07 (Erzeugung), 01.08 (Commit) | MC-TC-Welle committet (`392734e`) | G2-Execution [C0] |
| SESSION_RULES v1→v2.0 | 20./22.07 → 01.08 (PB-03) | v2.0-Kette + Checklist | G4-M2 [C0] |
| Handovers | 11.–27.07 original, 28./30./31.07 Backfill | 17/17 (PB-01) | SESSION_CONTINUITY, G4-M3 [C0] |

## 8. Major Transitions (nur belegte)

| Übergang | Beleg | Datum |
|----------|-------|-------|
| MCXF-Interpreter → Execution-Graph-Compiler | D-001 + ADR-001 (MAS-0301) | 04.07 [C0] |
| `simulation_mode: bool` → `ExecutionMode`-Enum | D-024 (OVERRIDE MC-TC-003B) | 25.07 [C1] |
| EventBus-only → EventStore-Persistenz | D-008 + Commits 19./20.07 + Replay | 19.–21.07 [C0] |
| „von Menschen entwickelt" → agentengetriebene Selbstentwicklung (Vision) | D-032 (S2 21.07) | 21.07 [C2] |
| „Prompt AST" → „Semantic AST / Cognitive IR" | Concept-Map §2 (reintroduced/renamed) | 30.07 [C2] |
| Audit-/Gate-Betrieb: Phase A → G2 → Phase B → G4/G4.5 → G5 → G6 → G7 | 08_REMEDIATION_GATE_HISTORY | 01.08 [C0] |
| M4-Metrik: Documentation Redundancy → Decision Completeness | G5-R6, G6-Recheck | 01.08 [C0] |

## 9. Persistent Open Questions (nur bestehende)

| # | Frage | Beleg | Typ |
|---|-------|-------|-----|
| P-1 | Ist MUSCAL ein OS, eine Sprache oder ein Framework? (alle 3 behauptet) | Concept-Map §4 (M-ROOT vs formale Spec) | Naming-Konflikt |
| P-2 | Ist ALITA Frontend von MUSCAL CORE oder eigenes Projekt? | §4 (S1 vs Repo) | Identitäts-Ambiguität |
| P-3 | Wo gehört KIR relativ zur Memory-Architektur? | §4 (KIR-Spec vs docs/memory/) | Spec-Layering |
| P-4 | Ist Graph-OS eigene Schicht oder MUSCAL-2.0-Frontend? | §4 (S2 23.–31.07) | Architektur |
| P-5 | D-010 vs D-001: Migrationspfad oder Koexistenz? | G7-03 (MEDIUM), Registry §D | Entscheidungs-Konflikt |
| P-6 | P5 Human Sovereignty vs Auto-Approve (gilt heute?) | G7-03 (MEDIUM) | Scope-Klärung |
| P-7 | S-2026-07-31-001 Detailinhalt | G4-M3 | UNKNOWN (GAP) |
| P-8 | MC-015→ADR-Konvertierung vollständig? | Registry §E (ADR-022 DRAFT) | Gap |

## 10. Validation

| Prüfpunkt | Ergebnis |
|-----------|----------|
| Erstauftritte nur mit Beleg | ✅ alle Timeline-Zeilen mit Quelle (Concept-Map §1 [C0/C2], Commits, S2-Daten) |
| Keine neuen Evolutionshypothesen | ✅ Stabilitäts-Tiers wörtlich aus Concept-Map §2; keine neuen |
| Keine Zukunftsprognosen | ✅ keine Vorhersagen; DRAFT-Status (ADR-022…25) unverändert |
| Keine Interpretation über Artefakte hinaus | ✅ offene Fragen P-1…P-8 nur zitiert; Metrikwechsel als Fakt (G5-R6) |
| Unbekanntes als GAP | ✅ KIR-Repo-Status, S-07-31, P-8 |
| Markdown only | ✅ docs/audit/11_TEMPORAL_ANALYSIS_FOUNDATION.md |

---

*Erstellt als Zeitordnung bestehender Belege — keine neue Hypothese, keine Prognose. Stand: 02.08.2026.*
