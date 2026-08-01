# MUSCAL MREIL Architecture Audit

## 1. Existing Metrics

| Source | Metrics Available | Format |
|---|---|---|
| `MREILCapture` | latency, token_usage, cpu_time, ram_peak, cpu_percent, ram_current | `ResourceMetrics` + `MREILMetric` |
| `EfficiencyEstimate` | quality_estimate, cost_estimate, latency_estimate, task_fit_score, confidence | `orchestration/models.py` |
| `RuntimeObservability` | All runtime/knowledge events in EventStore | SQLite append-only |
| `BridgeVerifier` | verification status, findings | `verification_report` dict |

## 2. Missing Measurements

| Gap | Needed For |
|---|---|
| Execution-level metrics (per execution_id) | Historical agent performance |
| Agent success rates per category | Adaptive selection |
| Quality-per-token/cpu/time ratios | Resource efficiency scoring |
| Verification confidence scores | Quality metrics |
| Agent profile aggregation | Performance memory |

## 3. Integration Points

| Point | Component | Direction |
|---|---|---|
| After verification | BridgeOutput | Metrics ← verification result |
| During agent selection | AgentSelector | Metrics → historical performance boost |
| During planning | ExecutionPlanner | Metrics → workflow recommendations |
| After evaluation | RuntimeObservability | Metrics → EventStore events |

## 4. Data Ownership

| Data | Owner | Readable By |
|---|---|---|
| Execution Metrics | `features/optimization/metrics.py` | Evaluator, Optimizer |
| Agent Profiles | `features/optimization/agent_profile.py` | Selector (via adapter) |
| MREIL Scores | `features/optimization/evaluator.py` | EventStore, Knowledge |
| Workflow Recommendations | `features/optimization/optimizer.py` | Human review |
| Raw MREIL captures | `features/execution/mreil.py` | Metrics collector |

## 5. Safety Boundaries

- Optimization layer **collects** metrics
- Optimization layer **evaluates** and **recommends**
- Optimization layer does NOT execute
- Agent profiles derived from EventStore — no manual truth
- Selection uses historical data as a factor, not sole authority
