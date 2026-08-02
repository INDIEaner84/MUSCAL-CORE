# KF-3 Decision Dependency Graph

- Datum: 02.08.2026
- Zweck: Abhängigkeiten der offenen Entscheidungsphase (read-only; nur belegte Kanten)
- Basis: KF3_DECISION_QUEUE.md, G4.5/G5/G6/G7, DECISION_CLOSURE_PACKAGE, Doc 16/Doc 18

---

## 1. Graph

```
RC-1 ──┬──> RC-6              (Re-Messung erst nach P0-Entscheidung, Doc 18 §2; G6-05)
       └──> D-033…D-035       (Plan-Dokumente hängen an P0-Entscheidung, G7-01; B3-Teil)
RC-2 ──┬──> HDR-002…004       (3 HDRs seit 20.07 blockiert, G5 R2; HDR-001 §7)
       └──> RC-6              (Re-Messung erst nach HDR-001, Doc 18 §2; G6-05)
RC-4a ──> Architektur-Dokumente  (ADR-022…025 DRAFT-Knoten in Doc 04/14; Akzeptanz
                                  blockiert Folge-Dokumente, KF-03)
RC-3 ───> Test Governance    (Doc 10 §5: 19 flaky/2.347/1; Baseline 470; D-042-Freigabe)
RC-5 ───> (keine RC-1-Kante) (M-2-Korrektur: D-033…D-035 = separater Doku-/Roadmap-Cluster, PLANNED + CHAT_ONLY; KIR = KG-01, M-3)
D-033…D-035 ──> docs/governance/ (Plan-Dokumente, Phase C, DOC; keine automatische Abhängigkeit von RC-1)
RC-6 ───> (keine Folge-Blocker; Ergebnis = Gate-Status/Score-Aktualisierung; Mess-Gate = RC-1 + RC-2 + RC-4a + RC-5-Bewertung, H-1)
```

## 2. Kanten (belegt)

| Kante | Beleg |
|---|---|
| RC-1 → RC-6 | Doc 18 §2: „neue Messung erst nach RC-1/RC-2"; G6-05; §RC-6-M4-Messpunkt (H-1: notwendige, nicht hinreichende Bedingung) |
| D-033…D-035 → docs/governance/ | G6_04_REGISTRY_COMPLETION (PLANNED, chat-only, C2, ohne Repo-Artefakt); §RC-5; M-2-Korrektur: keine Kante RC-1 → D-033…D-035 (G7-01 verweist nicht auf D-033…D-035; Doc 16 B3/RC-1 ohne Bezug) |
| RC-2 → HDR-002…004 | G5 R2; DECISION_CLOSURE_PACKAGE §RC-2 („entblockt HDR-002…004") |
| RC-2 → RC-6 | Doc 18 §2; G6-05 |
| RC-4a → Architektur-Dokumente | KF-03 (keine Akzeptanzannahmen — blockiert Akzeptanz-Bezug, nicht die Dokumente; L-3-Korrektur); Doc 04 §5/§10, Doc 14 §6 (DRAFT-Knoten); DECISION_CLOSURE_PACKAGE §RC-4 |
| RC-3 → Test Governance | Doc 10 §5/§7; FL01A_FLAKINESS_REGISTER; D-042 (GLOBAL_STATE_ARCHITECTURE_DECISION_DRAFT) |
| RC-5 → (keine) | M-2-Korrektur: D-033…D-035 ≠ RC-1 (G6_04_REGISTRY_COMPLETION, §RC-5, G7-01 ohne Bezug); KIR = KG-01, keine Queue-Aufnahme (M-3) |
| RC-6 → (keine) | G4.5/G7-04: Gate-Status abhängig von RC-1/RC-2, nicht umgekehrt |

## 3. Eigenschaften

- **Einstiegspunkte:** RC-1 und RC-2 (beide Human/ARB, unabhängig voneinander entscheidbar; vorgegebene Struktur: RC-1 | RC-2 | RC-4a | RC-3 als parallele Wurzeln).
- **Kritischer Pfad:** RC-1 bzw. RC-2 → RC-6 → Score-/Gate-Aktualisierung (formeller >75-Nachweis).
- **Parallel möglich:** RC-4a (Review) und RC-5 (Doku-Arbeiten ohne Entscheidung) hängen nicht automatisch an RC-1 (M-2: D-033…D-035-Cluster entkoppelt); F-03-Prüfung ist unabhängig.
- **Keine neuen Kanten:** Nur die oben belegten Abhängigkeiten; keine Reihenfolge-Empfehlung impliziert.

## 4. Validation

- Read-only: keine Entscheidung, keine Empfehlung, keine Score-Berechnung; alle Kanten mit Quelle (G5/G6/G7/Doc 16/Doc 18/DECISION_CLOSURE_PACKAGE).
- Konsistenz: deckungsgleich mit KF3_DECISION_QUEUE.md (§Abhängigkeiten) und Doc 16 §5 (RC-Tabelle).
