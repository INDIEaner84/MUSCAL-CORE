# MUSCAL Event Bus Routing Rules

## Zweck

Routing-Regeln für die Weiterleitung von Events an die richtigen Subscriber.

---

## Routing Methoden

### 1. Topic-Based Routing

```yaml
Topic Routing:
  Strategy: Events werden an alle Subscriber des Topics gesendet
  
  Example:
    Topic: task.created
    Subscribers: [AGT-004, AGT-009, AGT-010]
    Delivery: Fan-out an alle Subscriber
```

### 2. Direct Routing

```yaml
Direct Routing:
  Strategy: Events werden direkt an einen bestimmten Agent gesendet
  
  Example:
    Target: AGT-005
    Delivery: Point-to-point
```

### 3. Content-Based Routing

```yaml
Content Routing:
  Strategy: Events werden basierend auf Inhalt geroutet
  
  Rules:
    - Field: payload.type
      Value: testing
      Target: AGT-009
    
    - Field: payload.type
      Value: documentation
      Target: AGT-010
```

### 4. Header-Based Routing

```yaml
Header Routing:
  Strategy: Events werden basierend auf Header geroutet
  
  Rules:
    - Header: x-agent-type
      Value: core
      Target: all_core_agents
    
    - Header: x-priority
      Value: critical
      Target: meta_orchestrator
```

---

## Routing Rules

### Standard Routing

```yaml
Standard Rules:
  # System Events
  system.*:
    Target: all_agents
    Strategy: broadcast
  
  # Agent Events
  agent.*:
    Target: meta_orchestrator
    Strategy: direct
  
  # Task Events
  task.created:
    Target: all_agents
    Strategy: broadcast
  
  task.assigned:
    Target: assigned_agent
    Strategy: direct
  
  task.completed:
    Target: meta_orchestrator
    Strategy: direct
  
  task.failed:
    Target: [meta_orchestrator, monitoring_agent]
    Strategy: fan-out
  
  # Knowledge Events
  knowledge.*:
    Target: memory_architect
    Strategy: direct
  
  # Security Events
  security.*:
    Target: [meta_orchestrator, guardian_agent]
    Strategy: fan-out
```

### Priority-Based Routing

```yaml
Priority Rules:
  critical:
    Target: meta_orchestrator
    Strategy: direct
    Queue: high_priority
    TTL: 60
  
  high:
    Target: assigned_agent
    Strategy: direct
    Queue: high_priority
    TTL: 300
  
  medium:
    Target: assigned_agent
    Strategy: direct
    Queue: default
    TTL: 3600
  
  low:
    Target: assigned_agent
    Strategy: direct
    Queue: low_priority
    TTL: 86400
```

---

## Filter Rules

```yaml
Filters:
  # Nur Events von bestimmten Agents
  Source Filter:
    Include: [AGT-004, AGT-005]
    Exclude: []
  
  # Nur Events mit bestimmtem Inhalt
  Content Filter:
    Field: payload.type
    Operator: equals
    Value: testing
  
  # Kombination aus mehreren Kriterien
  Combined Filter:
    - Field: source
      Operator: in
      Value: [AGT-004, AGT-005]
    - Field: payload.priority
      Operator: equals
      Value: high
```

---

## Dead Letter Handling

```yaml
Dead Letter Rules:
  Max Retries: 3
  Retry Delay: exponential (1s, 2s, 4s)
  
  After Max Retries:
    Action: move_to_dead_letter
    Alert: true
    Notify: [meta_orchestrator, monitoring_agent]
  
  Dead Letter Queue:
    TTL: 7 days
    Max Size: 10000
    Cleanup: daily
```

---

## Monitoring

```yaml
Routing Metrics:
  - Events routed per second
  - Routing latency
  - Dead letter count
  - Failed deliveries
  - Queue sizes
```

---

## Dokumente

```
docs/eventbus/
├── ROUTING.md
├── ROUTING_RULES.yaml
├── FILTERS.md
└── DEAD_LETTER.md
```
