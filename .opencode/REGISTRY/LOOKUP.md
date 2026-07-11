# MUSCAL Agent Lookup Protocol

## Zweck

Protokoll für die Suche und Auswahl von Agenten aus der Registry.

---

## Lookup Methoden

### By ID

```bash
GET /api/registry/agents/{agent_id}
```

### By Name

```bash
GET /api/registry/agents?name={name}
```

### By Type

```bash
GET /api/registry/agents?type={type}
```

### By Capability

```bash
GET /api/registry/lookup/by-capability/{capability}
```

### By Status

```bash
GET /api/registry/agents?status={status}
```

---

## Suchalgorithmen

### Exact Match

```yaml
Strategy: Exact
  - Name: exact match
  - ID: exact match
  - Version: exact match
```

### Fuzzy Match

```yaml
Strategy: Fuzzy
  - Name: contains, similar
  - Description: contains keywords
  - Capabilities: partial match
```

### Weighted Search

```yaml
Strategy: Weighted
  Weights:
    Name: 40%
    Capabilities: 30%
    Type: 20%
    Status: 10%
```

---

## Agent Auswahl

### Für Aufgaben

```yaml
Task Assignment:
  1. Identify required capabilities
  2. Query agents with matching capabilities
  3. Filter by status (active only)
  4. Rank by:
     - Capability match score
     - Current workload
     - Recent performance
     - Cost
  5. Select best candidate
```

### Für Kollaboration

```yaml
Collaboration Selection:
  1. Identify primary agent
  2. Query agents with complementary capabilities
  3. Check compatibility
  4. Verify availability
  5. Form collaboration team
```

---

## Ranking Algorithmen

### Capability Match Score

```python
def capability_match_score(agent, required_capabilities):
    agent_caps = set(agent.capabilities)
    required_caps = set(required_capabilities)
    
    match = len(agent_caps.intersection(required_caps))
    total = len(required_caps)
    
    return match / total if total > 0 else 0
```

### Workload Score

```python
def workload_score(agent):
    # Lower workload = higher score
    active_tasks = get_active_tasks(agent.id)
    max_tasks = agent.max_concurrent_tasks
    
    return 1 - (active_tasks / max_tasks)
```

### Performance Score

```python
def performance_score(agent):
    metrics = get_agent_metrics(agent.id)
    
    # Higher success rate = higher score
    success_rate = metrics.success_rate
    
    # Lower avg duration = higher score
    duration_score = 1 / (1 + metrics.avg_duration_ms / 1000)
    
    return (success_rate + duration_score) / 2
```

---

## Lookup Beispiele

### Alle aktiven Core Agenten

```bash
curl "http://localhost:8080/api/registry/agents?type=core&status=active"
```

### Agenten mit Security-Fähigkeiten

```bash
curl "http://localhost:8080/api/registry/lookup/by-capability/security_scanning"
```

### Beste Agenten für Testing

```bash
curl "http://localhost:8080/api/registry/lookup?capability=test_generation&sort=performance&order=desc"
```

---

## Cache

```yaml
Cache Strategy:
  TTL: 5 minutes
  Invalidation:
    - On agent update
    - On status change
    - On capability change
  
  Warm-up:
    - On registry startup
    - On cache miss
```

---

## Dokumente

```
docs/registry/
├── LOOKUP.md
├── SEARCH_ALGORITHMS.md
├── RANKING.md
└── CACHING.md
```
