# MUSCAL Monitoring Dashboards

## Zweck

Dashboard-Design für die Systemüberwachung.

---

## Dashboard Übersicht

| Dashboard | Zielgruppe | Aktualisierung |
|-----------|------------|----------------|
| System Overview | Ops Team | 15s |
| Application | Development | 30s |
| Agents | Agent Managers | 1m |
| Business | Management | 5m |

---

## System Overview Dashboard

```yaml
System Overview:
  Panels:
    - Title: CPU Usage
      Type: Graph
      Metric: cpu_usage_percent
      Thresholds:
        - 80: warning
        - 95: critical
    
    - Title: Memory Usage
      Type: Graph
      Metric: memory_usage_percent
      Thresholds:
        - 80: warning
        - 95: critical
    
    - Title: Disk Usage
      Type: Gauge
      Metric: disk_usage_percent
      Thresholds:
        - 90: warning
        - 95: critical
    
    - Title: Network I/O
      Type: Graph
      Metrics:
        - network_in_bytes
        - network_out_bytes
    
    - Title: System Load
      Type: Graph
      Metric: load_average
```

---

## Application Dashboard

```yaml
Application Dashboard:
  Panels:
    - Title: Request Rate
      Type: Graph
      Metric: http_requests_total
      GroupBy: endpoint
    
    - Title: Error Rate
      Type: Graph
      Metric: http_errors_total
      GroupBy: endpoint
      Thresholds:
        - 5%: warning
        - 10%: critical
    
    - Title: Latency (P50, P95, P99)
      Type: Graph
      Metrics:
        - http_request_duration_seconds{quantile="0.5"}
        - http_request_duration_seconds{quantile="0.95"}
        - http_request_duration_seconds{quantile="0.99"}
    
    - Title: Active Requests
      Type: Stat
      Metric: http_requests_in_progress
    
    - Title: Response Codes
      Type: PieChart
      Metric: http_requests_total
      GroupBy: status_code
```

---

## Agent Dashboard

```yaml
Agent Dashboard:
  Panels:
    - Title: Agent Status
      Type: Table
      Metrics:
        - agent_up
        - agent_status
      GroupBy: agent_id
    
    - Title: Task Success Rate
      Type: Graph
      Metric: agent_tasks_successful / agent_tasks_total
      GroupBy: agent_id
      Thresholds:
        - 90%: warning
        - 80%: critical
    
    - Title: Response Time
      Type: Graph
      Metric: agent_response_time_seconds
      GroupBy: agent_id
    
    - Title: Token Usage
      Type: Graph
      Metric: agent_token_usage_total
      GroupBy: agent_id
    
    - Title: Cost
      Type: Stat
      Metric: agent_cost_total
      GroupBy: agent_id
    
    - Title: Active Tasks
      Type: Stat
      Metric: agent_tasks_active
      GroupBy: agent_id
```

---

## Business Dashboard

```yaml
Business Dashboard:
  Panels:
    - Title: Tasks Completed
      Type: Stat
      Metric: tasks_completed_total
    
    - Title: Success Rate
      Type: Gauge
      Metric: tasks_successful / tasks_total
      Thresholds:
        - 90%: warning
        - 80%: critical
    
    - Title: Cost
      Type: Stat
      Metric: total_cost
      Format: currency
    
    - Title: User Satisfaction
      Type: Stat
      Metric: user_satisfaction_score
    
    - Title: Tasks by Type
      Type: PieChart
      Metric: tasks_completed_total
      GroupBy: type
    
    - Title: Tasks Over Time
      Type: Graph
      Metric: tasks_completed_total
      GroupBy: day
```

---

## Alerting Rules

```yaml
Alerting:
  On Each Dashboard:
    - Show current alerts
    - Show alert history
    - Quick links to incident response
  
  Notification:
    - Slack channel per dashboard
    - Email digest daily
    - PagerDuty for critical
```

---

## Dokumente

```
monitoring/
├── DASHBOARDS.md
├── dashboards/
│   ├── system_overview.json
│   ├── application.json
│   ├── agents.json
│   └── business.json
└── provisioning/
    └── dashboards/
```
