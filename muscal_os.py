import dataclasses
import os
import sys
import time
from typing import Any, Dict, Optional

from boot_manager import BootManager, BootPhase, BootReport
from cognitive_diff import CognitiveDiffEngine
from event_bus import EventBus, EventPriority
from kernel import MuscalKernel
from runtime.event_store import EventStore
from kernel_diff_engine import KernelDiffEngine, StateStore, link_trace_to_state
from os_config import DeploymentMode, MuscalConfig, load_config
from schema import (
    EVENT_BOOT_INIT,
    EVENT_EDGE_CREATED,
    EVENT_EXECUTION_FINISHED,
    EVENT_EXECUTION_STARTED,
    EVENT_KERNEL_INITIALIZED,
    EVENT_NODE_CREATED,
    EVENT_NODE_UPDATED,
    EVENT_PLUGINS_INITIALIZED,
    EVENT_RUNTIME_INITIALIZED,
    EVENT_RUNTIME_SKIPPED,
    EVENT_SYSTEM_ACTION_COMPLETED,
    EVENT_SYSTEM_ACTION_FAILED,
    EVENT_SYSTEM_ACTION_STARTED,
)
from trace_engine import TraceEngine


class MuscalOS:
    def __init__(self, config: Optional[MuscalConfig] = None):
        self.config = config or load_config()
        self.boot = BootManager()
        self.events = EventBus()
        self.kernel: Optional[MuscalKernel] = None
        self._running = False
        self._start_time = 0.0
        self._boot_report: Optional[BootReport] = None
        self._last_mcxf: Optional[Dict] = None
        self.trace = TraceEngine()
        self._state_store = StateStore()
        self._kernel_diff = KernelDiffEngine()
        self.event_store: Optional[EventStore] = None

    def start(self) -> BootReport:
        self._start_time = time.time()
        self.boot.reset()
        self.trace.log("OBSERVABILITY", "BOOT_START", {"mode": self.config.mode.value}, trace_level=0)

        self.boot.run_phase(BootPhase.INIT, [
            ("create_storage", lambda: self._ensure_storage()),
            ("init_event_store", lambda: self._init_event_store()),
            ("init_event_bus", lambda: self._init_event_bus()),
        ])

        if self.boot.phase == BootPhase.FAILED:
            return self._finalize()

        self.boot.run_phase(BootPhase.LOAD_CONFIG, [
            ("validate_config", lambda: self._validate_config()),
            ("resolve_paths", lambda: self._resolve_paths()),
        ])

        if self.boot.phase == BootPhase.FAILED:
            return self._finalize()

        self.boot.run_phase(BootPhase.INIT_MODULES, [
            ("init_kernel", lambda: self._init_kernel()),
            ("init_plugins", lambda: self._init_plugins()),
            ("init_system_runtime", lambda: self._init_system_runtime()),
        ])

        if self.boot.phase == BootPhase.FAILED:
            return self._finalize()

        self.boot.run_phase(BootPhase.START_SERVICES, [
            ("wire_event_bus", lambda: self._wire_event_bus()),
            ("load_snapshot", lambda: self._load_snapshot()),
        ])

        if self.boot.phase == BootPhase.FAILED:
            return self._finalize()

        self.boot.run_phase(BootPhase.HEALTH_CHECK, [
            ("check_memory_db", lambda: self._health_check_memory()),
            ("check_graph", lambda: self._health_check_graph()),
            ("check_sphere", lambda: self._health_check_sphere()),
            ("check_tools", lambda: self._health_check_tools()),
        ])

        if self.boot.phase != BootPhase.FAILED:
            self.boot.phase = BootPhase.READY

        self._boot_report = self._finalize()
        if self._boot_report.success:
            self._running = True
            self.trace.log("OBSERVABILITY", "BOOT_READY", {"duration": self._boot_report.total_duration}, trace_level=0)
            self.events.publish("os.started", {
                "mode": self.config.mode.value,
                "duration": self._boot_report.total_duration,
            }, source="muscal_os", priority=EventPriority.HIGH)
        return self._boot_report

    def shutdown(self) -> BootReport:
        if not self._running:
            return BootReport(success=True, final_phase=BootPhase.SHUTDOWN)
        self._running = False
        self.trace.log("OBSERVABILITY", "SHUTDOWN", {"uptime": time.time() - self._start_time}, trace_level=0)
        self.boot.reset()
        self.boot.run_phase(BootPhase.SHUTDOWN, [
            ("save_snapshot", lambda: self._save_snapshot()),
            ("close_storage", lambda: True),
            ("flush_events", lambda: self.events.clear() or True),
        ])
        self.boot.phase = BootPhase.SHUTDOWN
        report = self.boot.get_report()
        self._boot_report = report
        self.events.publish("os.stopped", {"uptime": time.time() - self._start_time},
                            source="muscal_os")
        self._close_event_store()
        return report

    def restart(self) -> BootReport:
        self.shutdown()
        return self.start()

    def run(self, input_text: str) -> Dict[str, Any]:
        if not self._running or self.kernel is None:
            return {"error": "OS not running", "success": False, "validation_status": "FAIL"}
        sim = self.config.simulation_mode

        self.trace.log("COMPUTE", "MKC_INPUT", {"input": input_text[:200]}, trace_level=1)
        if sim:
            self.events.publish("os.simulate", {"input": input_text},
                                source="muscal_os")

        result = self.kernel.run(input_text)

        if result.success and result.mcxf is not None:
            mcxf_current = {
                "decisions": [dataclasses.asdict(t) for t in result.mcxf.decisions],
                "tasks": [dataclasses.asdict(t) for t in result.mcxf.tasks],
                "architecture": [dataclasses.asdict(t) for t in result.mcxf.architecture],
                "constraints": [dataclasses.asdict(t) for t in result.mcxf.constraints],
                "open_questions": list(result.mcxf.open_questions),
            }
        else:
            mcxf_current = {"decisions": [], "tasks": [],
                            "architecture": [], "constraints": [],
                            "open_questions": [f"MKC compile failed: {result.errors}"]}

        self.trace.log("COMPUTE", "MCXF_OUTPUT", {
            "decisions": len(mcxf_current.get("decisions", [])),
            "tasks": len(mcxf_current.get("tasks", [])),
        }, trace_level=1)

        mcxf_previous = self._last_mcxf or mcxf_current
        self._last_mcxf = mcxf_current

        diff_engine = CognitiveDiffEngine()
        diff_report = diff_engine.diff(mcxf_previous, mcxf_current)
        self.trace.log("OBSERVABILITY", "STATE_DIFF", {
            "recommendation": diff_report.recommendation,
            "changes": len(diff_report.logical_diff) + len(diff_report.behavioral_diff),
        }, trace_level=0)

        recommendation = diff_report.recommendation
        validation_status = "FAIL" if recommendation == "ROLLBACK" else "PASS"

        self.events.publish("os.executed", {
            "input": input_text,
            "success": result.success,
            "memory_id": result.memory_id,
            "validation": validation_status,
            "diff_recommendation": recommendation,
        }, source="muscal_os")

        return {
            "mcxf": mcxf_current,
            "diff": {
                "logical_diff": [
                    {"diff_type": e.diff_type, "section": e.section,
                     "field": e.field, "old_value": str(e.old_value),
                     "new_value": str(e.new_value), "impact": e.impact,
                     "description": e.description}
                    for e in diff_report.logical_diff
                ],
                "behavioral_diff": [
                    {"diff_type": e.diff_type, "section": e.section,
                     "field": e.field, "old_value": str(e.old_value),
                     "new_value": str(e.new_value), "impact": e.impact,
                     "description": e.description}
                    for e in diff_report.behavioral_diff
                ],
                "architectural_diff": [
                    {"diff_type": e.diff_type, "section": e.section,
                     "field": e.field, "old_value": str(e.old_value),
                     "new_value": str(e.new_value), "impact": e.impact,
                     "description": e.description}
                    for e in diff_report.architectural_diff
                ],
                "risk_analysis": [
                    {"risk_type": r.risk_type, "severity": r.severity,
                     "signal": r.signal, "mitigation": r.mitigation}
                    for r in diff_report.risk_analysis
                ],
                "recommendation": recommendation,
            },
            "validation_status": validation_status,
            "success": result.success,
            "execution": result.execution,
            "memory_id": result.memory_id,
            "feedback": result.feedback.summary,
            "errors": result.errors,
            "simulation": sim,
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "running": self._running,
            "uptime": time.time() - self._start_time if self._running else 0.0,
            "mode": self.config.mode.value,
            "simulation": self.config.simulation_mode,
            "boot": self._boot_report.summary if self._boot_report else "never booted",
            "events": self.events.get_stats(),
            "kernel_ready": self.kernel is not None,
            "event_store": self.event_store is not None,
        }

    def _ensure_storage(self) -> bool:
        os.makedirs(self.config.storage_path, exist_ok=True)
        return os.path.isdir(self.config.storage_path)

    def _init_event_store(self) -> bool:
        try:
            self.event_store = EventStore()
            self.events.subscribe("*", self._persist_to_store)
            return True
        except Exception as e:
            if self.boot.steps:
                self.boot.steps[-1].error = str(e)
            return False

    def _persist_to_store(self, msg) -> None:
        if self.event_store is None:
            return
        try:
            self.event_store.append({
                "topic": msg.topic,
                "payload": msg.payload,
                "source": msg.source,
                "priority": msg.priority,
                "timestamp": msg.timestamp,
                "id": msg.id,
            })
        except Exception:
            pass

    def _close_event_store(self) -> None:
        if self.event_store is not None:
            try:
                self.event_store.close()
            except Exception:
                pass
            self.event_store = None

    def _init_event_bus(self) -> bool:
        self.events.publish(EVENT_BOOT_INIT, {}, source="muscal_os")
        return True

    def _validate_config(self) -> bool:
        valid_modes = [e.value for e in DeploymentMode]
        return self.config.mode.value in valid_modes

    def _resolve_paths(self) -> bool:
        self.config.storage_path = os.path.abspath(self.config.storage_path)
        self.config.memory_db = os.path.abspath(self.config.memory_db)
        self.config.log_file = os.path.abspath(self.config.log_file)
        return True

    def _init_kernel(self) -> bool:
        try:
            self.kernel = MuscalKernel(
                enable_graph=self.config.enable_graph,
                enable_sphere=self.config.enable_sphere,
            )
            self.events.publish(EVENT_KERNEL_INITIALIZED, {
                "graph": self.config.enable_graph,
                "sphere": self.config.enable_sphere,
            }, source="muscal_os")
            return True
        except Exception as e:
            self.boot.steps[-1].error = str(e)
            return False

    def _init_plugins(self) -> bool:
        try:
            from plugin_loader import load_plugins
            from plugin_registry import PLUGINS
            load_plugins()
            self.events.publish(EVENT_PLUGINS_INITIALIZED, {
                "count": len(PLUGINS)
            }, source="muscal_os")
            return True
        except Exception as e:
            if self.boot.steps:
                self.boot.steps[-1].error = str(e)
            return False

    def _init_system_runtime(self) -> bool:
        if not self.config.enable_system_runtime:
            return True
        try:
            from system_runtime import SystemAgentRuntime
            rt = SystemAgentRuntime()
            ok = rt is not None
            self.events.publish(EVENT_RUNTIME_INITIALIZED, {
                "browser": self.config.enable_browser,
                "desktop": self.config.enable_desktop,
                "simulation": self.config.simulation_mode,
            }, source="muscal_os")
            return ok
        except ImportError:
            self.events.publish(EVENT_RUNTIME_SKIPPED, {"reason": "system_runtime not available"},
                                source="muscal_os")
            return True

    def _wire_event_bus(self) -> bool:
        if self.kernel is None or self.kernel.graph is None:
            return True
        graph = self.kernel.graph
        event_map = {
            EVENT_NODE_CREATED: "graph.node_created",
            EVENT_NODE_UPDATED: "graph.node_updated",
            EVENT_EDGE_CREATED: "graph.edge_created",
            EVENT_EXECUTION_STARTED: "graph.execution_started",
            EVENT_EXECUTION_FINISHED: "graph.execution_finished",
        }
        for graph_evt, bus_topic in event_map.items():
            graph.on(graph_evt, lambda e, t=bus_topic: self.events.publish(t, e, source="graph"))

        # ── EventBus → Graph bridge (Phase 2, ADR-003) ──────────────
        self.events.subscribe("*", self._bridge_to_graph)
        return True

    def _bridge_to_graph(self, msg) -> None:
        if self.kernel is None or self.kernel.graph is None:
            return
        payload = dict(msg.payload)
        payload["_source"] = msg.source
        self.kernel.graph.emit(msg.topic, payload)

    def _load_snapshot(self) -> bool:
        path = self.config.snapshot_file
        if os.path.isfile(path):
            self.events.publish("snapshot.loaded", {"path": path}, source="muscal_os")
        else:
            self.events.publish("snapshot.missing", {"path": path}, source="muscal_os")
        return True

    def _health_check_memory(self) -> bool:
        if self.kernel is None:
            return False
        try:
            from memory import search as mem_search
            results = mem_search("test", top_k=1)
            self.events.publish("health.memory", {"status": "ok"}, source="muscal_os")
            return isinstance(results, list)
        except Exception:
            self.events.publish("health.memory", {"status": "degraded"}, source="muscal_os")
            return True

    def _health_check_graph(self) -> bool:
        if self.kernel is None or self.kernel.graph is None:
            return True
        g = self.kernel.graph
        try:
            snap = g.get_snapshot()
            healthy = isinstance(snap, dict)
            self.events.publish("health.graph", {"ok": healthy, "nodes": len(g.nodes)},
                                source="muscal_os")
            return healthy
        except Exception:
            return False

    def _health_check_sphere(self) -> bool:
        if self.kernel is None or self.kernel.sphere is None:
            return True
        try:
            snap = self.kernel.sphere.get_snapshot()
            healthy = isinstance(snap, dict)
            self.events.publish("health.sphere", {"ok": healthy}, source="muscal_os")
            return healthy
        except Exception:
            return False

    def _health_check_tools(self) -> bool:
        try:
            from tools import TOOL_REGISTRY, TOOL_SCHEMAS
            available = len(TOOL_REGISTRY)
            schemas = len(TOOL_SCHEMAS)
            self.events.publish("health.tools", {"registry": available, "schemas": schemas},
                                source="muscal_os")
            return available > 0
        except Exception:
            return False

    def _save_snapshot(self) -> bool:
        if self.kernel is None:
            return True
        try:
            import json

            from kernel_snapshot import get_kernel_snapshot
            snap = get_kernel_snapshot(version=f"muscal_core_{self.config.mode.value}")
            with open(self.config.snapshot_file, "w") as f:
                json.dump(snap, f, indent=2)
            return True
        except Exception:
            return False

    def _finalize(self) -> BootReport:
        report = self.boot.get_report()
        if report.success:
            self.boot.phase = BootPhase.READY
        return report
