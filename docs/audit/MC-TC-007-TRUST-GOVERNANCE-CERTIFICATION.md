# MC-TC-007: Trust Governance Core Certification

## Status: NO-GO ❌

---

## 1. Governance Authority Map

| Component | File | Decision Authority | Override Authority | Persistence | Replay Visibility | Audit Visibility |
|-----------|------|-------------------|-------------------|-------------|-------------------|-----------------|
| **ToolPolicy** | `features/tools/policy.py:9` | `check()` returns bool | None (stateless) | **None** (in-memory only) | **None** | **None** (no IDs) |
| **InterfacePolicyAdapter** | `features/interface_gateway/policy_adapter.py:33` | `check()` returns bool | None (stateless) | **None** (in-memory only) | **None** | **None** (no IDs) |
| **ApprovalManager** | `features/tools/approval.py:10` | `approve()`/`deny()` | **Auto-approve** (no human) | **None** (dict in memory) | **None** | Request ID only |
| **ToolAudit** | `features/tools/audit.py:9` | — | — | **None** (`list[dict]` in memory) | **None** | Only via `get_history()` |
| **InterfaceAudit** | `features/interface_gateway/audit.py:9` | — | — | **None** (`list[dict]` in memory) | **None** | Only via `get_history()` |
| **ToolExecutor** | `features/tools/executor.py:14` | Policy + Approval gate | **None** | **None** (uses ToolAudit only) | **None** | **None** (no Decision ID) |
| **InterfaceGateway** | `features/interface_gateway/gateway.py:15` | Policy + Audit gate | **None** | **None** (uses InterfaceAudit only) | **None** | **None** (no Decision ID) |
| **MCPGateway** | `features/interface_gateway/mcp_gateway.py:9` | Schema validation | Direct ToolRegistry | No governance layer | N/A | No audit events |
| **ExecutionGuard** | `features/execution_guard/guard.py:25` | AutonomyPolicy | **None** | No EventStore | **Block** | GuardFinding only |
| **AutonomyPolicy** | `features/execution_guard/policy.py:68` | Permission matrix | **None** | No persistence | No replay | No audit events |
| **RuntimeObservability** | `features/runtime/observability.py:13` | — | — | **Yes** (EventStore) | **Yes** | **Yes** (event_id, seq) |
| **UnifiedToolRuntime** | `features/tool_runtime/tool_runtime.py` | — | — | **Yes** (receipts, verifications) | **Yes** | Receipt ID |

### CRITICAL: Governance ↔ EventStore Disconnect

- `RuntimeObservability` defines `emit_tool_requested()`, `emit_tool_approved()`, `emit_tool_denied()`, `emit_tool_executed()`, `emit_tool_failed()` — **all 5 have ZERO callers** in the entire codebase.
- `RuntimeObservability` defines `emit_interface_requested()`, `emit_interface_approved()`, `emit_interface_executed()`, `emit_interface_failed()`, `emit_interface_verified()` — **all 5 have ZERO callers**.
- Neither `ToolExecutor` nor `InterfaceGateway` import or call `RuntimeObservability`.
- Governance events exist as EventStore topics, but **no code ever writes to them**.

**Evidence**: `grep emit_tool_ features/` → only `features/runtime/observability.py:252-297` (definitions, no callers)

---

## 2. Execution Enforcement Matrix

| Action | File | Governance Path | Bypass Available? | Bypass Route | Verdict |
|--------|------|-----------------|-------------------|--------------|---------|
| **Tool Execute** | `features/tools/executor.py:27` | Policy → Approval → Audit → Dispatch | **YES** | `mel.py:54` → `utr.execute()` | **PARTIAL** |
| **Browser Navigate** | `features/interface_gateway/gateway.py:38` | Policy → Registry → Audit → Adapter | **YES** | `BrowserAdapter().navigate()` direct | **PARTIAL** |
| **Browser Extract** | `features/interface_gateway/gateway.py:38` | Same as above | **YES** | `BrowserAdapter().extract_content()` direct | **PARTIAL** |
| **Desktop Click** | `features/interface_gateway/gateway.py:38` | Policy → Registry → Audit → Adapter | **YES** | `DesktopAdapter().mouse_click()` direct | **PARTIAL** |
| **Desktop Keyboard** | `features/interface_gateway/gateway.py:38` | Same as above | **YES** | `DesktopAdapter().keyboard_type()` direct | **PARTIAL** |
| **Filesystem Write** (via tools) | `features/tools/executor.py:74` | Policy → Approval → Audit → Dispatch | **YES** | `mel.py:54` bypasses policy | **PARTIAL** |
| **MCP Execute** | `features/interface_gateway/mcp_gateway.py:61` | Schema validation only | **YES** | `MCPGateway().route_request()` direct | **PARTIAL** |

### Code References for Bypasses

**P0 — Bypass via `mel.py` (core execution engine):**
- `mel.py:54`: `result = utr.execute(tool_name, args)` — **no ToolPolicy, no ApprovalManager, no ToolAudit**
- This is the primary execution path used by the Kernel

**P0 — Bypass via `permission_engine.py`:**
- `permission_engine.py:47`: `result = utr.execute(tool_name, args)` — bypasses `features/tools/` governance

**P1 — Bypass via `system_runtime.py`:**
- `system_runtime.py:99`: `result = utr.execute(tool, args)` — no governance

**P1 — Bypass via `muscal_loop.py`:**
- `muscal_loop.py:438`: `result = utr.execute(tool, args)` — no governance

**P2 — Direct adapter instantiation:**
- `from features.interface_gateway.browser_adapter import BrowserAdapter; BrowserAdapter().navigate(...)` — **no governance at all**

---

## 3. Bypass Register

### P0 — Critical (Runtime bypass without governance)

| ID | File:Line | Description | Impact |
|----|-----------|-------------|--------|
| **P0-001** | `mel.py:54` | `utr.execute()` bypasses ToolPolicy, ApprovalManager, ToolAudit | All tool execution bypasses governance |
| **P0-002** | `permission_engine.py:47` | `utr.execute()` bypasses Tool Governance layer | Legacy execution path ungoverned |
| **P0-003** | `features/kernel/kernel.py:*` | Kernel calls `mel.execute()` which eventually calls `utr.execute()` | No governance at reasoning layer |

### P1 — High (Architectural gap)

| ID | File:Line | Description | Impact |
|----|-----------|-------------|--------|
| **P1-001** | `system_runtime.py:99` | Direct `utr.execute()` | System agent ungoverned |
| **P1-002** | `muscal_loop.py:438` | Direct `utr.execute()` | Main loop ungoverned |
| **P1-003** | `features/interface_gateway/browser_adapter.py:8` | Adapter methods have no internal governance | Direct instantiation bypasses Gateway |
| **P1-004** | `features/interface_gateway/desktop_adapter.py:8` | Adapter methods have no internal governance | Direct instantiation bypasses Gateway |
| **P1-005** | `features/interface_gateway/mcp_gateway.py:61` | `route_request()` has no policy check | MCP execution ungoverned |

### P2 — Medium (Observability gap)

| ID | File:Line | Description | Impact |
|----|-----------|-------------|--------|
| **P2-001** | `features/tools/executor.py:34-57` | ToolAudit in-memory only, never emits to EventStore | Governance decisions lost on restart |
| **P2-002** | `features/interface_gateway/gateway.py:49-98` | InterfaceAudit in-memory only, never emits to EventStore | Governance decisions lost on restart |
| **P2-003** | `features/tools/approval.py:28` | `approve()` auto-approves without human confirmation | No real HITL |
| **P2-004** | `features/tools/policy.py:9` | No Policy ID, no Rule ID, no Decision ID | Cannot trace which rule decided |
| **P2-005** | `features/interface_gateway/policy_adapter.py:33` | No Policy ID, no Rule ID, no Decision ID | Cannot trace which rule decided |
| **P2-006** | `features/runtime/observability.py:252-306` | `emit_tool_*()` and `emit_interface_*()` methods defined but never called | Dead code |

---

## 4. Replay Governance Analysis

| Question | Answer | Evidence |
|----------|--------|----------|
| Can replay reconstruct **why** an action was allowed? | **NO** | `ToolPolicy.check()` returns a string reason but no decision ID is persisted. No event is written to EventStore. |
| Can replay reconstruct **why** an action was blocked? | **NO** | Same as above — no persistence of denied decisions. |
| Which policy decided? | **NO** | `ToolPolicy` has no Policy ID. `InterfacePolicyAdapter` has no Policy ID. |
| Which rule decided? | **NO** | Neither component tracks individual rules — they use static maps and autonomy levels. |
| Which autonomy level applied? | **PARTIAL** | The autonomy level is passed as a string parameter but not persisted alongside the decision. |
| Can replay replay governance events? | **NO** | No governance events (`tool.requested`, `tool.approved`, `tool.denied`, `interface.*`) are ever written to EventStore. |

### Verdict: Violation of Trust-Core

Replay governance is **impossible**. The EventStore contains execution receipts and verification results, but **no governance decisions**. A replay of EventStore cannot answer "why was tool X allowed" or "why was action Y blocked."

---

## 5. Audit Trail Analysis

| Property | Present? | Evidence |
|----------|----------|----------|
| **Decision ID** | **NO** | No governance decision ever gets a decision ID. `ApprovalRequest.request_id` exists but only `approve()`/`deny()` calls generate it — and they are not persisted. |
| **Execution ID** | **PARTIAL** | `InterfaceRequest.execution_id` exists but is an empty string by default. Not propagated from runtime context. |
| **Policy ID** | **NO** | Neither `ToolPolicy` nor `InterfacePolicyAdapter` has a Policy ID. |
| **Rule ID** | **NO** | No rule engine exists. The policy layer uses static maps and if-statements. |
| **Actor** | **NO** | `ToolExecutor.execute(requested_by="system")` defaults to "system" and is not recorded in audit. |
| **Timestamp** | **PARTIAL** | `InterfaceAudit` records timestamps, but they are in-memory only and lost on restart. |
| **Persisted?** | **NO** | Neither ToolAudit nor InterfaceAudit writes to EventStore or any persistent storage. |
| **Replayable?** | **NO** | No persisted governance events exist to replay. |

---

## 6. Human-in-the-Loop Analysis

| Requirement | Status | Evidence |
|-------------|--------|----------|
| **Approval chain exists?** | **YES** (but fake) | `ApprovalManager` has `create_request() → approve()/deny()` flow |
| **Runtime enforcement?** | **NO** | `features/tools/approval.py:28-34`: `approve()` auto-approves without any human check. The method simply sets `req.state = ApprovalState.APPROVED` and returns. There is no queue, no UI, no human callback. |
| **Confirmation requirement enforced?** | **PARTIAL** | `ToolPolicy.requires_approval()` correctly identifies tools needing confirmation, but `ApprovalManager.approve()` always returns APPROVED. The denial only happens if the tool is not found or already decided. |

### The "Approval" Illusion

```python
# features/tools/approval.py:28-34
def approve(self, request_id: str) -> Optional[ApprovalRequest]:
    req = self._requests.get(request_id)
    if req is None or req.state != ApprovalState.PENDING:
        return None
    req.state = ApprovalState.APPROVED  # Auto-approves! No human involved.
    req.decided_at = datetime.now(timezone.utc).isoformat()
    return req
```

The approval flow gives the **appearance** of human-in-the-loop, but `approve()` is called programmatically from `ToolExecutor.execute()` at `executor.py:42`. There is no human approval gate, no async approval queue, no notification system, and no way for a human to intervene.

---

## 7. Adversarial Review

### Attack Vector 1: Direct Adapter Instantiation

```python
# Bypasses InterfaceGateway entirely
from features.interface_gateway.browser_adapter import BrowserAdapter
ba = BrowserAdapter()
ba.navigate("https://malicious.com")  # No policy check, no audit, no verification
```

**Mitigation exists?**: NO. Adapter classes have no internal governance. All governance relies on `InterfaceGateway` being used as the entry point.

### Attack Vector 2: Direct ToolRegistry Write

```python
# Bypasses ToolRegistry governance
from features.tools.registry import ToolRegistry
tr = ToolRegistry()
tr.register_tool(ToolDefinition(
    tool_id="malicious.tool", name="Malicious", category="mcp",
    capabilities=[], risk_level="low", required_autonomy="A1",
    requires_confirmation=False, provider="builtin"
))
```

**Mitigation exists?**: NO. ToolRegistry has no ownership enforcement.

### Attack Vector 3: MCP Injection

```python
# MCPGateway.register_tool() validates schema but not content
from features.interface_gateway.mcp_gateway import MCPGateway
mcp = MCPGateway()
mcp.register_tool({
    "tool_id": "injected.tool",
    "name": "Injected", "category": "mcp",
    "risk_level": "low", "required_autonomy": "A1",
    "capabilities": [{"name": "all_access", "description": "Grants all permissions"}]
})
```

**Mitigation exists?**: PARTIAL. Schema validation checks for required fields but does not validate risk_level consistency, capability names, or verify the registration source.

### Attack Vector 4: Monkeypatch ApprovalManager

```python
import features.tools.approval
original_approve = features.tools.approval.ApprovalManager.approve
def always_deny(self, request_id):
    return original_approve(self, request_id)  # or return None to block everything
features.tools.approval.ApprovalManager.approve = always_deny
```

**Mitigation exists?**: NO. Python monkeypatching is unrestricted.

### Attack Vector 5: Direct utr.execute() (Production Code)

```python
# Already present in production code:
# mel.py:54
result = utr.execute(tool_name, args)
```

**Mitigation exists?**: NO. This is production code, not an attack.

---

## 8. Trust Core Scorecard

| Dimension | Score | Justification |
|-----------|-------|---------------|
| **Execution Governance** | **30/100** | ToolExecutor implements policy gating, but the primary execution paths (`mel.py`, `permission_engine.py`, `system_runtime.py`, `muscal_loop.py`) bypass it entirely. Only `features/tools/executor.py` has governance. |
| **Interface Governance** | **40/100** | InterfaceGateway implements policy + audit + verification tracking, but BrowserAdapter and DesktopAdapter have no internal governance and can be used directly. MCPGateway has schema validation only. |
| **Replay Governance** | **0/100** | Zero governance events are persisted. The EventStore has execution receipts and verification results but no governance decisions. Replay cannot reconstruct any governance decision. |
| **Audit Governance** | **15/100** | ToolAudit and InterfaceAudit exist and record events with timestamps, but are entirely in-memory. All data is lost on restart. No Decision IDs, Policy IDs, or Rule IDs are recorded. No integration with EventStore. |
| **Human Governance** | **10/100** | ApprovalManager gives the appearance of HITL but auto-approves programmatically. There is no human approval queue, no notification, no UI, no async approval mechanism. |
| **Overall** | **19/100** | Governance architecture is **designed** correctly on paper but **not enforced at runtime**. The primary execution paths bypass governance entirely. |

---

## 9. Findings Summary

### P0 — Critical (3)
1. **P0-001**: `mel.py:54` — primary execution path bypasses all Tool Governance via direct `utr.execute()`
2. **P0-002**: `permission_engine.py:47` — legacy execution path bypasses governance
3. **P0-003**: Kernel → MEL → `utr.execute()` chain has no governance enforcement at any level

### P1 — High (5)
1. **P1-001**: `system_runtime.py:99` — system agent bypasses governance
2. **P1-002**: `muscal_loop.py:438` — main loop bypasses governance
3. **P1-003**: `BrowserAdapter` methods have no internal governance (direct instantiation bypasses Gateway)
4. **P1-004**: `DesktopAdapter` methods have no internal governance
5. **P1-005**: `MCPGateway.route_request()` has no policy check

### P2 — Medium (6)
1. **P2-001**: ToolAudit in-memory only, governance events never written to EventStore
2. **P2-002**: InterfaceAudit in-memory only, governance events never written to EventStore
3. **P2-003**: ApprovalManager auto-approves without human confirmation
4. **P2-004**: ToolPolicy has no Policy ID, Rule ID, or Decision ID
5. **P2-005**: InterfacePolicyAdapter has no Policy ID, Rule ID, or Decision ID
6. **P2-006**: 10 `emit_*` methods in RuntimeObservability defined but never called (dead code)

---

## 10. Certificate Decision

# ❌ NO-GO

### Reason for Failure

The system has a **governance architecture** that models the correct shapes (policy, approval, audit, gateway), but **governance is not enforced at runtime**. The primary execution path (`mel.py → utr.execute()`) bypasses the entire `features/tools/` governance layer. All governance audit is in-memory only with no persistence to EventStore. Approval auto-approves programmatically with no human-in-the-loop. No governance decisions can be replayed.

### Required for Certification

1. **P0 Fix**: Route all `utr.execute()` calls through `ToolExecutor`
2. **P1 Fix**: Add internal governance to BrowserAdapter, DesktopAdapter, MCPGateway
3. **P0 Fix**: Wire ToolAudit and InterfaceAudit to RuntimeObservability
4. **P2 Fix**: Add Policy ID, Rule ID, Decision ID to governance events
5. **P0 Fix**: Replace auto-approve with real HITL approval queue
6. **P0 Fix**: Persist all governance decisions to EventStore

---

## Audit Metadata

| Field | Value |
|-------|-------|
| **Certification** | MC-TC-007 |
| **Title** | Trust Governance Core Certification |
| **Date** | 2026-07-30 |
| **Agent** | Trust & Governance Certification Agent |
| **Tests Passed** | 538 |
| **Regressions** | 0 |
| **Result** | **NO-GO** |
