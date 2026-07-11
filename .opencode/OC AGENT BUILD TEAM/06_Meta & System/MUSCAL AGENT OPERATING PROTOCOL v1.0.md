# MUSCAL AGENT OPERATING PROTOCOL v1.0 (MAOP)

## Zweck

Dies ist der Standardvertrag, den jeder zukünftige Agent erfüllen muss, um automatisch in das MUSCAL Ökosystem aufgenommen zu werden.

---

## 1. Agent Identität

Jeder Agent muss sich identifizieren:

```yaml
Agent Identity:
  Name: [einzigartiger name]
  Version: [semver]
  Typ: [core / governance / business / ops]
  Verantwortungsbereich: [text]
  Autor: [text]
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
  5. Berichte Status
```

### Session Ende

```yaml
Session End:
  1. Aktualisiere AGENT_STATUS.md
  2. Dokumentiere Entscheidungen
  3. Speichere Learning
  4. Definiere nächste Schritte
  5. Berichte Abschluss
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
```

### Output Format

```yaml
Agent Response:
  ID: [task id]
  Status: [completed / in_progress / blocked]
  Ergebnis: [text]
  Metriken: [text]
  Empfehlungen: [text]
  Nächste Schritte: [text]
```

---

## 4. Wissens-Protokoll

### Wissen speichern

```yaml
Knowledge Entry:
  Kategorie: [text]
  Thema: [text]
  Inhalt: [text]
  Quelle: [text]
  Vertrauenslevel: [hoch / mittel / niedrig]
  Gültig bis: [datum]
```

### Wissen abfragen

```yaml
Knowledge Query:
  Kategorie: [text]
  Thema: [text]
  Tiefe: [oberfläche / detailliert]
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
    - Option B: [text]
      Vorteile: [text]
      Nachteile: [text]
  
  Empfehlung: [A/B]
  Begründung: [text]
  Risiko: [text]
  Genehmigung: [ausstehend / genehmigt / abgelehnt]
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
```

---

## 7. Performance-Metriken

```yaml
Performance:
  Aufgaben erledigt: [anzahl]
  Erfolgsrate: [%]
  Durchschnittliche Bearbeitungszeit: [sekunden]
  Token-Verbrauch: [anzahl]
  Kosten: [EUR]
  Qualität: [score]
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

---

## 9. Sicherheits-Protokoll

```yaml
Security:
  - [ ] Keine Geheimnisse im Klartext
  - [ ] Audit-Trail für alle Aktionen
  - [ ] Rollback für alle Änderungen
  - [ ] Genehmigung für kritische Aktionen
  - [ ] Verschlüsselung für sensible Daten
```

---

## 10. Governance

```yaml
Governance:
  Constitution: MUSCAL Constitution Guardian
  Ethics: MUSCAL Ethics Compliance Agent
  Cost: MUSCAL Cost Optimizer
  Audit: MUSCAL Benchmark Evolution Agent
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
