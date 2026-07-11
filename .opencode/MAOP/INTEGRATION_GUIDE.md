# MUSCAL MAOP Integration Guide

## Zweck

Schritt-für-Schritt-Anleitung zur Integration eines neuen Agenten in das MUSCAL Ökosystem.

---

## Voraussetzungen

```yaml
Prerequisites:
  - Python 3.10+
  - Zugang zur Agent Registry
  - Zugang zum Event Bus
  - Zugang zum Shared Memory
  - Verständnis des MAOP Protokolls
```

---

## Integration Steps

### Step 1: Agent Definition erstellen

```yaml
# agent_definition.yaml
Agent:
  Name: MeinAgent
  ID: AGT-XXX
  Type: core  # core / governance / business / ops
  Version: 1.0.0
  
  Capabilities:
    - capability_1
    - capability_2
  
  Dependencies:
    - dependency_1
  
  Endpoints:
    input: /agents/mein-agent/input
    output: /agents/mein-agent/output
    status: /agents/mein-agent/status
```

### Step 2: Bei Registry registrieren

```bash
# Registration via API
curl -X POST http://localhost:8080/api/registry/agents \
  -H "Content-Type: application/json" \
  -d @agent_definition.yaml
```

### Step 3: Event Bus Subscription

```yaml
Subscriptions:
  - topic: task.created
    filter: "type == 'mein-agent-type'"
    callback: handle_task
  
  - topic: system.alert
    callback: handle_alert
```

### Step 4: Shared Memory Integration

```yaml
Memory Integration:
  Read:
    - architecture_decisions
    - coding_standards
    - api_contracts
  
  Write:
    - agent_status
    - decisions
    - discoveries
```

### Step 5: Status Endpoint implementieren

```python
@app.get("/agents/{agent_id}/status")
async def get_status():
    return {
        "agent_id": "AGT-XXX",
        "status": "active",
        "last_active": datetime.now(),
        "metrics": {
            "tasks_completed": 0,
            "success_rate": 100.0,
            "avg_duration_ms": 0
        }
    }
```

### Step 6: Task Handler implementieren

```python
@app.post("/agents/{agent_id}/tasks")
async def handle_task(task: Task):
    try:
        # Task verarbeiten
        result = await process_task(task)
        
        # Ergebnis melden
        await report_result(task.id, result)
        
        # Metriken aktualisieren
        await update_metrics(task.id, result)
        
        return result
    except Exception as e:
        await report_error(task.id, e)
        raise
```

### Step 7: Testing

```bash
# Unit Tests
pytest tests/unit/

# Integration Tests
pytest tests/integration/

# E2E Tests
pytest tests/e2e/
```

### Step 8: Deployment

```yaml
Deployment:
  Environment: staging
  Strategy: canary
  Rollback: automatic
  
  Steps:
    - deploy_to_staging
    - run_smoke_tests
    - monitor_30_minutes
    - deploy_to_production
```

---

## Integration Checklist

```yaml
Checklist:
  Pre-Integration:
    - [ ] Agent Definition erstellt
    - [ ] MAOP gelesen und verstanden
    - [ ] Abhängigkeiten installiert
    - [ ] Tests geschrieben
  
  During Integration:
    - [ ] Registry Registration erfolgreich
    - [ ] Event Bus Subscription funktioniert
    - [ ] Shared Memory Zugriff funktioniert
    - [ ] Status Endpoint antwortet
    - [ ] Task Handler funktioniert
  
  Post-Integration:
    - [ ] Unit Tests bestanden
    - [ ] Integration Tests bestanden
    - [ ] Documentation aktualisiert
    - [ ] Team informiert
    - [ ] Monitoring konfiguriert
```

---

## Troubleshooting

| Problem | Lösung |
|---------|--------|
| Registry nicht erreichbar | Service-Status prüfen |
| Event Bus Subscription fehlgeschlagen | Topic und Filter prüfen |
| Shared Memory Zugriff verweigert | Berechtigungen prüfen |
| Status Endpoint antwortet nicht | Firewall und Ports prüfen |
| Task Handler wirft Fehler | Logs prüfen |

---

## Dokumentation

```
docs/maop/
├── INTEGRATION_GUIDE.md
├── TROUBLESHOOTING.md
├── EXAMPLES/
└── FAQ.md
```
