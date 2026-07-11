# MUSCAL EVENT BUS

## Zweck

Zentrale Kommunikationsplattform für alle Agenten.

---

## Architektur

```
Publisher
    │
    ▼
┌─────────────────┐
│    Event Bus    │
│  (Message Hub)  │
└─────────────────┘
    │
    ▼
Subscriber
```

---

## Event Types

| Type | Beschreibung | Beispiel |
|------|--------------|----------|
| Command | Aufforderung zur Aktion | process_task |
| Query | Anfrage nach Information | get_agent_status |
| Event | Benachrichtigung | task_completed |
| Error | Fehlermeldung | task_failed |

---

## Event Format

```yaml
Event:
  ID: [unique id]
  Type: [command/query/event/error]
  Source: [agent name]
  Target: [agent name / broadcast]
  Timestamp: [iso8601]
  
  Payload:
    Action: [action name]
    Data: [任意データ]
  
  Metadata:
    Priority: [low/medium/high/critical]
    TTL: [time to live]
    Reply-To: [callback topic]
```

---

## Event Topics

| Topic | Beschreibung |
|-------|--------------|
| agent.registry | Agent Registrierung |
| agent.status | Agent Status Updates |
| task.created | Neue Aufgaben |
| task.completed | Aufgaben abgeschlossen |
| task.failed | Aufgaben fehlgeschlagen |
| system.alert | System Alerts |
| system.metrics | System Metriken |
| knowledge.updated | Wissens Updates |

---

## Publish/Subscribe

```yaml
Publish:
  Topic: [topic name]
  Event: [event data]
  
Subscribe:
  Topic: [topic name]
  Filter: [optional filter]
  Callback: [handler function]
```

---

## Event Processing

```yaml
Processing:
  Modes:
    - Synchronous: warte auf Response
    - Asynchronous: fire and forget
    - Ordered: Reihenfolge beibehalten
    - Transactional: mit Rollback
  
  Retries:
    Max: 3
    Backoff: exponential
    Delay: 1s, 2s, 4s
  
  Dead Letter Queue:
    Enabled: true
    Max Retries: 3
    Alert: true
```

---

## Event Routing

```yaml
Routing:
  Direct:
    Target: specific agent
    Method: point-to-point
  
  Broadcast:
    Target: all agents
    Method: publish-subscribe
  
  Filtered:
    Target: agents with capability
    Method: topic-based
```

---

## Monitoring

```yaml
Monitoring:
  Metrics:
    - Events per second
    - Processing time
    - Error rate
    - Queue size
  
  Alerts:
    - Queue size > 1000
    - Processing time > 1s
    - Error rate > 1%
```

---

## Dokumente

```
docs/eventbus/
├── EVENT_BUS_ARCHITECTURE.md
├── EVENT_SCHEMA.md
├── TOPIC_REGISTRY.md
├── EVENT_PROCESSING.md
└── EVENT_MONITORING.md
```

---

## Abschluss

Event Throughput: __ events/s

Average Processing Time: __ms

Nächster Schritt: _______________
