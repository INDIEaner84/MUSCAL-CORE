# MUSCAL Architecture Decision Records

| ID | Titel | Status | Date |
|----|-------|--------|------|
| ADR-001 | [Kernel Runtime — Single Pipeline Authority](./ADR-001-kernel.md) | APPLIED | 2026-07-08 |
| ADR-002 | [Memory — GraphMemory als Standard-Interface](./ADR-002-memory.md) | ACCEPTED (Ph1-4 ✅) | 2026-07-08 |
| ADR-003 | [Event System — EventBus als Standard](./ADR-003-events.md) | APPLIED | 2026-07-08 |
| ADR-004 | [Plugin System — Hook-Based Extensions](./ADR-004-plugins.md) | ACCEPTED | 2026-07-08 |
| ADR-005 | [Pipeline Architecture — Monolithic Data Flow](./ADR-005-pipeline.md) | ACCEPTED | 2026-07-08 |
| ADR-006 | [Graph/Sphere — Event-Driven Execution Graph](./ADR-006-graph.md) | ACCEPTED | 2026-07-08 |
| ADR-007 | [Core Immutability — Write Guard Policy](./ADR-007-immutability.md) | ACCEPTED | 2026-07-08 |
| ADR-013 | [Feature Plugin Migration Path (historisch)](./ADR-013-pipeline.md) | Superseded by ADR-007 | 2026-07-08 |
| ADR-008 | [Deployment Runtime — Supervisor Container Model](./ADR-008-deployment.md) | ACCEPTED | 2026-07-08 |
| ADR-009 | [Observability Foundation](./ADR-009-observability.md) | ACCEPTED | 2026-07-10 |
| ADR-010 | [SQLite Consolidation — Unified Single Database](./ADR-010-sqlite.md) | APPLIED | 2026-07-10 |
| ADR-011 | [Verification Layer Architecture](./ADR-011-verification.md) | ACCEPTED | 2026-07-11 |
| ADR-012 | [Event Persistence — Audit Log + Replay](./ADR-012-event-persistence.md) | APPLIED | 2026-07-11 |
| ADR-014 | [Unified Tool Runtime](./ADR-014-tool-runtime.md) | PROPOSED | 2026-07-15 |

## Status Definitions

- **PROPOSED** — Vorgeschlagen, noch nicht umgesetzt
- **ACCEPTED** — Akzeptiert, Umsetzung begonnen
- **APPLIED** — Umsetzung abgeschlossen
- **DEPRECATED** — Nicht mehr gültig
- **SUPERSEDED** — Durch neueres ADR ersetzt

## Template

Neue ADRs folgen dem Format:

```markdown
# ADR-NNN: Titel

**Status:** PROPOSED  
**Date:** YYYY-MM-DD  

## Context
## Decision
## Migration Plan
## Consequences
## Compliance Check
```
