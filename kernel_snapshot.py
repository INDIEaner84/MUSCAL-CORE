"""
MUSCAL Kernel Cognitive Snapshot v0.1

Read-only introspection of the live kernel state.
Captures all decision-making parameters without modifying anything.

Usage:
    snap = get_kernel_snapshot(version="muscal_core_v0.1")
    with open("snapshot.json", "w") as f:
        json.dump(snap, f, indent=2)
"""

import time

from bridge import MATCHERS
from feedback import analyze_feedback
from mkc_rules import (
    CONFIDENCE_RANGE,
    CONFIDENCE_THRESHOLD,
    CONSECUTIVE_FAILURES_RESET,
    IGNORED_KEYWORDS,
    MAX_KEYWORD_ADDITIONS,
    SECTION_FALLBACK,
    SIGNAL_RULES,
    get_signal_rules_snapshot,
)
from schema import (
    EVENT_SYSTEM_ACTION_COMPLETED,
    EVENT_SYSTEM_ACTION_FAILED,
    EVENT_SYSTEM_ACTION_STARTED,
    MCXF_REQUIRED_KEYS,
)
from tools import TOOL_REGISTRY, TOOL_SCHEMAS


def _get_type_name(t):
    if isinstance(t, tuple):
        return " | ".join(x.__name__ for x in t)
    return t.__name__


def get_kernel_snapshot(version="unknown") -> dict:
    return {
        "version": version,
        "timestamp": time.time(),
        "signal_rules": get_signal_rules_snapshot(),
        "ignored_keywords": list(IGNORED_KEYWORDS),
        "section_fallback": SECTION_FALLBACK,
        "confidence": {
            "range": dict(CONFIDENCE_RANGE),
            "threshold": CONFIDENCE_THRESHOLD,
        },
        "feedback": {
            "consecutive_failures_reset": CONSECUTIVE_FAILURES_RESET,
            "max_keyword_additions": MAX_KEYWORD_ADDITIONS,
        },
        "tool_registry": {
            "count": len(TOOL_REGISTRY),
            "names": sorted(TOOL_REGISTRY.keys()),
        },
        "tool_schemas": {
            name: {
                "input": {p: _get_type_name(t) for p, t in schema["input"].items()},
                "output": {p: _get_type_name(t) for p, t in schema["output"].items()},
                "constraints": list(schema.get("constraints", [])),
            }
            for name, schema in TOOL_SCHEMAS.items()
        },
        "bridge_patterns": [
            {
                "name": matcher.__name__,
                "doc": (matcher.__doc__ or "").strip(),
            }
            for matcher in MATCHERS
        ],
        "modules": {
            "mkc": {
                "classifier": "rule_based",
                "signal_sections": len(SIGNAL_RULES),
                "fallback": SECTION_FALLBACK,
            },
            "mel": {
                "dispatch": "TOOL_REGISTRY + SystemAgentRuntime",
                "tools_available": len(TOOL_REGISTRY),
            },
            "bridge": {
                "matchers": len(MATCHERS),
            },
            "memory": {
                "type": "sqlite + jsonl",
                "tables": ["memory", "mcxf_store"],
            },
            "rag": {
                "strategy": "chronological",
                "top_k_default": 3,
            },
            "graph": {
                "node_types": [
                    "INTENT", "MKC_STEP", "MCXF_SECTION",
                    "EXECUTION_PLAN", "TOOL_EXECUTION",
                    "MEMORY_ENTRY", "RAG_CONTEXT", "CONFLICT",
                    "SYSTEM_ACTION",
                ],
                "edge_types": [
                    "DERIVES_FROM", "EXECUTES", "DEPENDS_ON",
                    "CONFLICTS_WITH", "RETRIEVES_FROM", "CONTROLS",
                ],
            },
            "sphere": {
                "rings": ["inner", "middle", "outer"],
            },
            "system_control": {
                "browser_available": False,
                "desktop_available": False,
            },
        },
        "event_types": [
            "NODE_CREATED", "NODE_UPDATED", "EDGE_CREATED",
            "EXECUTION_STARTED", "EXECUTION_FINISHED",
            "SYSTEM_ACTION_STARTED", "SYSTEM_ACTION_COMPLETED",
            "SYSTEM_ACTION_FAILED",
        ],
        "mcxf_schema": {
            "format_version": "1.0",
            "required_sections": list(MCXF_REQUIRED_KEYS),
            "triple_fields": ["section", "subject", "predicate", "object"],
            "open_questions_type": "list[str]",
        },
    }
