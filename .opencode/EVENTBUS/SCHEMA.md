# MUSCAL Event Bus Schema Definition

## Zweck

Standardisierte Schema-Definition für alle Events im Event Bus.

---

## Event Structure

```yaml
Event:
  # Header
  ID: [uuid]
  Type: [command/query/event/error]
  Topic: [topic.path]
  Source: [agent_id]
  Target: [agent_id / broadcast]
  
  # Timestamps
  Created: [iso8601]
  Expires: [iso8601]
  
  # Content
  Payload: [object]
  
  # Metadata
  Metadata:
    CorrelationID: [uuid]
    ReplyTo: [topic]
    Priority: [low/medium/high/critical]
    TTL: [seconds]
    ContentType: [application/json]
  
  # Trace
  Trace:
    SpanID: [uuid]
    ParentSpanID: [uuid]
    TraceFlags: [bitmask]
```

---

## Event Types

### Command

```yaml
Command Event:
  Type: command
  Purpose: Aufforderung zur Aktion
  
  Payload:
    Action: [action_name]
    Parameters: [object]
  
  Example:
    ID: cmd-123
    Type: command
    Topic: task.created
    Source: AGT-004
    Target: AGT-009
    Payload:
      Action: process_task
      Parameters:
        TaskID: task-456
        Type: testing
        Priority: high
```

### Query

```yaml
Query Event:
  Type: query
  Purpose: Anfrage nach Information
  
  Payload:
    Query: [query_string]
    Parameters: [object]
  
  Example:
    ID: qry-123
    Type: query
    Topic: knowledge.queried
    Source: AGT-005
    Target: AGT-001
    Payload:
      Query: "get_architecture_decisions"
      Parameters:
        Limit: 10
```

### Event

```yaml
Notification Event:
  Type: event
  Purpose: Benachrichtigung über Ereignis
  
  Payload:
    Event: [event_name]
    Data: [object]
  
  Example:
    ID: evt-123
    Type: event
    Topic: task.completed
    Source: AGT-009
    Target: broadcast
    Payload:
      Event: task_completed
      Data:
        TaskID: task-456
        Result: success
        Duration: 1234
```

### Error

```yaml
Error Event:
  Type: error
  Purpose: Fehlermeldung
  
  Payload:
    Error: [error_object]
    Context: [object]
  
  Example:
    ID: err-123
    Type: error
    Topic: agent.error
    Source: AGT-009
    Target: AGT-004
    Payload:
      Error:
        Code: TEST_FAILED
        Message: "Unit test failed"
        Stack: [traceback]
      Context:
        TaskID: task-456
        TestName: test_process
```

---

## Validation Rules

```yaml
Validation:
  ID:
    Type: UUID
    Required: true
  
  Type:
    Enum: [command, query, event, error]
    Required: true
  
  Topic:
    Pattern: "[a-z]+\\.[a-z]+"
    Required: true
  
  Source:
    Pattern: "AGT-[0-9]{3}"
    Required: true
  
  Created:
    Format: ISO8601
    Required: true
  
  Payload:
    Type: object
    Required: true
```

---

## Error Codes

| Code | Beschreibung |
|------|--------------|
| AGENT_NOT_FOUND | Ziel-Agent nicht gefunden |
| TASK_FAILED | Aufgabe fehlgeschlagen |
| VALIDATION_ERROR | Event-Validierung fehlgeschlagen |
| TIMEOUT | Zeitüberschreitung |
| PERMISSION_DENIED | Keine Berechtigung |
| RESOURCE_NOT_FOUND | Ressource nicht gefunden |
| INTERNAL_ERROR | Interner Fehler |

---

## Beispiele

### Task Created Event

```json
{
  "ID": "evt-789",
  "Type": "event",
  "Topic": "task.created",
  "Source": "AGT-004",
  "Target": "broadcast",
  "Created": "2026-07-10T12:00:00Z",
  "Payload": {
    "Event": "task_created",
    "Data": {
      "TaskID": "task-012",
      "Name": "Implement new feature",
      "Type": "implementation",
      "Priority": "high",
      "AssignedTo": "AGT-005"
    }
  },
  "Metadata": {
    "CorrelationID": "corr-456",
    "Priority": "high",
    "TTL": 3600
  }
}
```
