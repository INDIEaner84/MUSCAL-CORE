import asyncio
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

logger = logging.getLogger(__name__)


class PolicyAction(str, Enum):
    ALLOW = "allow"
    WARN = "warn"
    BLOCK = "block"
    ESCALATE = "escalate"


@dataclass
class GovernanceLimits:
    max_tokens_per_session: int = 100_000
    max_iterations: int = 25
    max_cost_usd: float = 2.00
    max_memory_writes: int = 100
    max_task_duration_seconds: float = 300.0
    human_in_loop_actions: list[str] = field(
        default_factory=lambda: [
            "filesystem_write",
            "external_api_call",
            "shell_execute",
        ]
    )


@dataclass
class UsageStats:
    agent_id: str = ""
    tokens_used: int = 0
    iterations: int = 0
    cost_usd: float = 0.0
    memory_writes: int = 0
    actions: list[str] = field(default_factory=list)


class Governance:
    def __init__(self, limits: Optional[GovernanceLimits] = None) -> None:
        self.limits = limits or GovernanceLimits()
        self._usage: dict[str, UsageStats] = {}
        self._violations: list[dict[str, Any]] = []
        self._lock = asyncio.Lock()

    def get_usage(self, agent_id: str) -> UsageStats:
        if agent_id not in self._usage:
            self._usage[agent_id] = UsageStats(agent_id=agent_id)
        return self._usage[agent_id]

    async def consume_iteration(self, agent_id: str) -> bool:
        async with self._lock:
            usage = self.get_usage(agent_id)
            if usage.iterations >= self.limits.max_iterations:
                await self._record_violation(
                    agent_id, "iteration_limit",
                    f"Exceeded {self.limits.max_iterations} iterations"
                )
                return False
            usage.iterations += 1
            return True

    async def check_tokens(self, agent_id: str, requested: int) -> PolicyAction:
        async with self._lock:
            usage = self.get_usage(agent_id)
            projected = usage.tokens_used + requested
            if projected > self.limits.max_tokens_per_session:
                await self._record_violation(
                    agent_id, "token_limit",
                    f"Would exceed {self.limits.max_tokens_per_session} tokens"
                )
                return PolicyAction.BLOCK
            elif projected > self.limits.max_tokens_per_session * 0.8:
                return PolicyAction.WARN
            return PolicyAction.ALLOW

    async def check_cost(self, agent_id: str, estimated_cost: float) -> PolicyAction:
        async with self._lock:
            usage = self.get_usage(agent_id)
            projected = usage.cost_usd + estimated_cost
            if projected > self.limits.max_cost_usd:
                await self._record_violation(
                    agent_id, "cost_limit",
                    f"Would exceed ${self.limits.max_cost_usd:.2f}"
                )
                return PolicyAction.BLOCK
            elif projected > self.limits.max_cost_usd * 0.8:
                return PolicyAction.WARN
            return PolicyAction.ALLOW

    async def check_human_in_loop(self, action: str) -> PolicyAction:
        if action in self.limits.human_in_loop_actions:
            return PolicyAction.ESCALATE
        return PolicyAction.ALLOW

    async def record_usage(
        self,
        agent_id: str,
        tokens: int = 0,
        cost: float = 0.0,
        action: Optional[str] = None,
    ) -> None:
        async with self._lock:
            usage = self.get_usage(agent_id)
            usage.tokens_used += tokens
            usage.cost_usd += cost
            if action:
                usage.actions.append(action)
                if action in self.limits.human_in_loop_actions:
                    logger.warning(
                        f"Agent {agent_id} performed HITL action: {action}"
                    )

    async def _record_violation(
        self, agent_id: str, violation_type: str, message: str
    ) -> None:
        violation = {
            "agent_id": agent_id,
            "type": violation_type,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._violations.append(violation)
        logger.warning(f"Governance violation: {agent_id} - {message}")

    def get_violations(self, agent_id: Optional[str] = None) -> list[dict[str, Any]]:
        if agent_id:
            return [v for v in self._violations if v["agent_id"] == agent_id]
        return list(self._violations)

    def get_all_usage(self) -> dict[str, UsageStats]:
        return dict(self._usage)

    def to_dict(self) -> dict[str, Any]:
        return {
            "limits": {
                "max_tokens_per_session": self.limits.max_tokens_per_session,
                "max_iterations": self.limits.max_iterations,
                "max_cost_usd": self.limits.max_cost_usd,
                "max_memory_writes": self.limits.max_memory_writes,
                "human_in_loop_actions": self.limits.human_in_loop_actions,
            },
            "usage": {
                aid: {
                    "tokens_used": u.tokens_used,
                    "iterations": u.iterations,
                    "cost_usd": u.cost_usd,
                    "memory_writes": u.memory_writes,
                }
                for aid, u in self._usage.items()
            },
            "violations_count": len(self._violations),
        }


class GovernanceSync:
    def __init__(self, limits: Optional[GovernanceLimits] = None) -> None:
        self.limits = limits or GovernanceLimits()
        self._usage: dict[str, UsageStats] = {}
        self._violations: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def get_usage(self, agent_id: str) -> UsageStats:
        if agent_id not in self._usage:
            self._usage[agent_id] = UsageStats(agent_id=agent_id)
        return self._usage[agent_id]

    def consume_iteration(self, agent_id: str) -> bool:
        with self._lock:
            usage = self.get_usage(agent_id)
            if usage.iterations >= self.limits.max_iterations:
                self._record_violation(
                    agent_id, "iteration_limit",
                    f"Exceeded {self.limits.max_iterations} iterations"
                )
                return False
            usage.iterations += 1
            return True

    def check_tokens(self, agent_id: str, requested: int) -> PolicyAction:
        with self._lock:
            usage = self.get_usage(agent_id)
            projected = usage.tokens_used + requested
            if projected > self.limits.max_tokens_per_session:
                self._record_violation(
                    agent_id, "token_limit",
                    f"Would exceed {self.limits.max_tokens_per_session} tokens"
                )
                return PolicyAction.BLOCK
            elif projected > self.limits.max_tokens_per_session * 0.8:
                return PolicyAction.WARN
            return PolicyAction.ALLOW

    def record_usage(
        self,
        agent_id: str,
        tokens: int = 0,
        cost: float = 0.0,
        action: Optional[str] = None,
    ) -> None:
        with self._lock:
            usage = self.get_usage(agent_id)
            usage.tokens_used += tokens
            usage.cost_usd += cost
            if action:
                usage.actions.append(action)
                if action in self.limits.human_in_loop_actions:
                    logger.warning(
                        f"Agent {agent_id} performed HITL action: {action}"
                    )

    def _record_violation(
        self, agent_id: str, violation_type: str, message: str
    ) -> None:
        violation = {
            "agent_id": agent_id,
            "type": violation_type,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._violations.append(violation)
        logger.warning(f"Governance violation: {agent_id} - {message}")

    def get_violations(self, agent_id: Optional[str] = None) -> list[dict[str, Any]]:
        if agent_id:
            return [v for v in self._violations if v["agent_id"] == agent_id]
        return list(self._violations)

    def get_all_usage(self) -> dict[str, UsageStats]:
        return dict(self._usage)

    def to_dict(self) -> dict[str, Any]:
        return {
            "limits": {
                "max_tokens_per_session": self.limits.max_tokens_per_session,
                "max_iterations": self.limits.max_iterations,
                "max_cost_usd": self.limits.max_cost_usd,
                "max_memory_writes": self.limits.max_memory_writes,
                "human_in_loop_actions": self.limits.human_in_loop_actions,
            },
            "usage": {
                aid: {
                    "tokens_used": u.tokens_used,
                    "iterations": u.iterations,
                    "cost_usd": u.cost_usd,
                    "memory_writes": u.memory_writes,
                }
                for aid, u in self._usage.items()
            },
            "violations_count": len(self._violations),
        }
