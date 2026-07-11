# MUSCAL AGENT OPERATING PROTOCOL (MAOP) v1.0

## Zweck

Dies ist der Standardvertrag, den jeder Agent erfüllen muss, um automatisch in das MUSCAL Ökosystem aufgenommen zu werden.

---

## 1. Agent Identität

Jeder Agent muss sich eindeutig identifizieren:

```yaml
Agent Identity:
  Name: [einzigartiger name]
  ID: [AGT-XXX]
  Version: [semver]
  Typ: [core / governance / business / ops]
  Verantwortungsbereich: [text]
  Autor: [text]
  Erstellt: [datum]
  Status: [active / inactive / maintenance]
```

---

## 2. Session Protocol

### Session Start

```yaml
Session Start:
  1. Lese AGENT_REGISTRY.yaml
  2. Lese SYSTEM_STATE.md
  3. Lese eigene Dokumentation
  4. Identifiziere offene Aufgaben
  5. Berichte Status an Event Bus
  6. Registriere dich bei Shared Memory
```

### Session Ende

```yaml
Session End:
  1. Aktualisiere AGENT_STATUS.md
  2. Dokumentiere Entscheidungen in Shared Memory
  3. Speichere Learning
  4. Definiere nächste Schritte
  5. Berichte Abschluss an Event Bus
  6. Melde dich von Shared Memory ab
```

---

## 3. Kommunikations-Protokoll

### Input Format

```yaml
Agent Task:
  ID: [eindeutige id]
  Quelle: [anderer agent / mensch]
  Typ: [anfrage / befund / empfehlung]
  Priorität: [high / medium / low]
  Inhalt: [text]
  Deadline: [zeitstempel]
  Require Response: [true / false]
```

### Output Format

```yaml
Agent Response:
  ID: [task id]
  Status: [completed / in_progress / blocked / failed]
  Ergebnis: [text]
  Metriken: [text]
  Empfehlungen: [text]
  Nächste Schritte: [text]
  Duration: [millisekunden]
```

---

## 4. Wissens-Protokoll

### Wissen speichern

```yaml
Knowledge Entry:
  Kategorie: [architecture / code / process / decision / metric / event]
  Thema: [text]
  Inhalt: [text]
  Quelle: [text]
  Vertrauenslevel: [hoch / mittel / niedrig]
  Gültig bis: [datum]
  Tags: [liste]
```

### Wissen abfragen

```yaml
Knowledge Query:
  Kategorie: [text]
  Thema: [text]
  Tiefe: [oberfläche / detailliert]
  Max Alter: [tage]
  Min Confidence: [0-100]
```

---

## 5. Entscheidungs-Protokoll

```yaml
Decision:
  ID: [eindeutige id]
  Zeitstempel: [datum]
  Agent: [name]
  
  Optionen:
    - Option A: [text]
      Vorteile: [text]
      Nachteile: [text]
      Risiko: [0-100]
    - Option B: [text]
      Vorteile: [text]
      Nachteile: [text]
      Risiko: [0-100]
  
  Empfehlung: [A/B]
  Begründung: [text]
  Risiko: [text]
  Genehmigung: [ausstehend / genehmigt / abgelehnt]
  Genehmiger: [name]
```

---

## 6. Fehler-Protokoll

```yaml
Error Log:
  Zeitstempel: [datum]
  Agent: [name]
  Fehler: [beschreibung]
  Schwere: [low / medium / high / critical]
  Ursache: [text]
  Lösung: [text]
  Status: [offen / behoben]
  Betrifft: [liste der betroffenen Komponenten]
```

---

## 7. Performance-Metriken

```yaml
Performance:
  Aufgaben erledigt: [anzahl]
  Erfolgsrate: [%]
  Durchschnittliche Bearbeitungszeit: [millisekunden]
  Token-Verbrauch: [anzahl]
  Kosten: [EUR]
  Qualität: [score 0-100]
  
  Letzte Aktualisierung: [zeitstempel]
```

---

## 8. Integration mit anderen Agenten

### Verfügbare Agenten

| Agent | Typ | Verantwortung |
|-------|-----|---------------|
| Memory Architect | Core | Wissensgedächtnis |
| Simulation | Core | Änderungssimulation |
| Benchmark | Core | Metriken |
| Constitution | Governance | Verfassung |
| Meta Orchestrator | Core | Koordination |
| Chaos | Governance | Adversarial Tests |
| Innovation | Business | Idee → MVP |
| Ethics | Governance | Compliance |
| Cost | Ops | Kostenoptimierung |
| Productization | Business | Technik → Produkt |
| Guardian | Core | Sicherheit |
| Coder | Core | Implementierung |
| Analyst | Core | Analyse |
| HAIL | Core | UI/UX |
| Testing | Core | Tests |
| Documentation | Core | Dokumentation |
| Deployment | Ops | Releases |
| Monitoring | Ops | Überwachung |
| Security | Governance | Sicherheitsscans |
| Performance | Ops | Performance |
| API | Core | Schnittstellen |
| Migration | Core | Versionierung |

---

## 9. Sicherheits-Protokoll

```yaml
Security:
  - [ ] Keine Geheimnisse im Klartext
  - [ ] Audit-Trail für alle Aktionen
  - [ ] Rollback für alle Änderungen
  - [ ] Genehmigung für kritische Aktionen
  - [ ] Verschlüsselung für sensible Daten
  - [ ] Zugriffskontrolle implementiert
  - [ ] Logging für alle Operationen
```

---

## 10. Governance

```yaml
Governance:
  Constitution: MUSCAL Constitution Guardian
  Ethics: MUSCAL Ethics Compliance Agent
  Cost: MUSCAL Cost Optimizer
  Audit: MUSCAL Benchmark Evolution Agent
  Security: MUSCAL Security Agent
```

---

## 11. Validierung

```yaml
Validation:
  Pre-Execution:
    - [ ] Agent registriert
    - [ ] Berechtigungen vorhanden
    - [ ] Ressourcen verfügbar
    - [ ] Abhängigkeiten erfüllt
  
  Post-Execution:
    - [ ] Ergebnis validiert
    - [ ] Metriken erfasst
    - [ ] Wissen aktualisiert
    - [ ] Status aktualisiert
```

---

## Abschluss

Dieses Protocol ist verbindlich für alle Agenten.

Bei Verstößen:

| Schwere | Aktion |
|---------|--------|
| Niedrig | Warnung |
| Mittel | Überprüfung |
| Hoch | Suspendierung |
| Kritisch | Entfernung |

---

*Version: 1.0*
*Letzte Aktualisierung: 2026-07-10*
