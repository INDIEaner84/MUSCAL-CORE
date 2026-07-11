# MUSCAL Event Bus Architecture

## Zweck

Technische Architektur des Event Bus für die inter-Agent-Kommunikation.

---

## Überblick

```
┌─────────────────────────────────────────────────────────┐
│                      Event Bus                          │
├─────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │
│  │Publisher│  │Subscriber│  │ Router  │  │ Queue   │   │
│  │ Manager │  │ Manager  │  │ Engine  │  │ Manager │   │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘   │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐   │
│  │              Message Broker                      │   │
│  │         (Redis / RabbitMQ / Kafka)              │   │
│  └─────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐   │
│  │              Persistence Layer                   │   │
│  │         (Event Store / Dead Letter Queue)       │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## Komponenten

### Publisher Manager

```yaml
Publisher Manager:
  Responsibilities:
    - Validate outgoing events
    - Assign event IDs
    - Set timestamps
    - Route to correct topic
    - Handle publish errors
  
  Features:
    - Async publishing
    - Batch publishing
    - Retry logic
    - Circuit breaker
```

### Subscriber Manager

```yaml
Subscriber Manager:
  Responsibilities:
    - Manage subscriptions
    - Deliver events to handlers
    - Handle acknowledgment
    - Manage dead letters
  
  Features:
    - Wildcard subscriptions
    - Filter expressions
    - Priority queues
    - Load balancing
```

### Router Engine

```yaml
Router Engine:
  Responsibilities:
    - Route events to subscribers
    - Apply routing rules
    - Handle fan-out
    - Manage topic hierarchies
  
  Features:
    - Content-based routing
    - Header-based routing
    - Topic-based routing
    - Dynamic routing
```

### Queue Manager

```yaml
Queue Manager:
  Responsibilities:
    - Manage message queues
    - Handle persistence
    - Implement TTL
    - Manage dead letters
  
  Features:
    - Priority queues
    - Delayed queues
    - Scheduled queues
    - Queue monitoring
```

---

## Message Broker

### Optionen

| Broker | Vorteile | Nachteile |
|--------|----------|-----------|
| Redis | Schnell, einfach | Begrenzte Features |
| RabbitMQ | Zuverlässig, flexibel | Komplexer |
| Kafka | Skalierbar, streaming | Overkill für kleinere Systeme |

### Empfehlung

```yaml
Recommended:
  Development: Redis
  Staging: Redis
  Production: RabbitMQ oder Kafka (je nach Skala)
```

---

## Event Flow

```
Publisher
    │
    ▼
[1] Validate Event
    │
    ▼
[2] Assign ID + Timestamp
    │
    ▼
[3] Route to Topic
    │
    ▼
[4] Persist (optional)
    │
    ▼
[5] Deliver to Subscribers
    │
    ▼
[6] Acknowledge
    │
    ▼
[7] Update Metrics
```

---

## Guarantees

```yaml
Delivery Guarantees:
  At Most Once:
    - Event may be lost
    - No duplicates
    - Fastest
  
  At Least Once:
    - Event delivered at least once
    - May have duplicates
    - Recommended
  
  Exactly Once:
    - Event delivered exactly once
    - No duplicates
    - Slowest

Default: At Least Once
```

---

## Performance

```yaml
Performance Targets:
  Latency:
    P50: <10ms
    P95: <50ms
    P99: <100ms
  
  Throughput:
    Events/sec: >10,000
    Bytes/sec: >100MB
  
  Availability:
    Uptime: 99.9%
    Recovery: <30s
```

---

## Monitoring

```yaml
Monitoring:
  Metrics:
    - Events published
    - Events delivered
    - Delivery latency
    - Queue size
    - Dead letter count
    - Error rate
  
  Alerts:
    - Queue size > 1000
    - Latency > 100ms
    - Error rate > 1%
    - Dead letters > 0
```

---

## Dokumente

```
docs/eventbus/
├── ARCHITECTURE.md
├── CONFIGURATION.md
├── DEPLOYMENT.md
└── TROUBLESHOOTING.md
```
