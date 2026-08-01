from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# ── Graph Node / Edge Types ──────────────────────────────────────────

NODE_TYPE_INTENT = "INTENT"
NODE_TYPE_MKC_STEP = "MKC_STEP"
NODE_TYPE_MCXF_SECTION = "MCXF_SECTION"
NODE_TYPE_EXECUTION_PLAN = "EXECUTION_PLAN"
NODE_TYPE_TOOL_EXECUTION = "TOOL_EXECUTION"
NODE_TYPE_MEMORY_ENTRY = "MEMORY_ENTRY"
NODE_TYPE_RAG_CONTEXT = "RAG_CONTEXT"
NODE_TYPE_CONFLICT = "CONFLICT"
NODE_TYPE_SYSTEM_ACTION = "SYSTEM_ACTION"

EDGE_TYPE_DERIVES_FROM = "DERIVES_FROM"
EDGE_TYPE_EXECUTES = "EXECUTES"
EDGE_TYPE_DEPENDS_ON = "DEPENDS_ON"
EDGE_TYPE_CONFLICTS_WITH = "CONFLICTS_WITH"
EDGE_TYPE_RETRIEVES_FROM = "RETRIEVES_FROM"
EDGE_TYPE_CONTROLS = "CONTROLS"

EVENT_NODE_CREATED = "NODE_CREATED"
EVENT_NODE_UPDATED = "NODE_UPDATED"
EVENT_EDGE_CREATED = "EDGE_CREATED"
EVENT_EXECUTION_STARTED = "EXECUTION_STARTED"
EVENT_EXECUTION_FINISHED = "EXECUTION_FINISHED"
EVENT_SYSTEM_ACTION_STARTED = "SYSTEM_ACTION_STARTED"
EVENT_SYSTEM_ACTION_COMPLETED = "SYSTEM_ACTION_COMPLETED"
EVENT_SYSTEM_ACTION_FAILED = "SYSTEM_ACTION_FAILED"

# ── OS-Lifecycle Events ───────────────────────────────────────────────
# ADR-003: Alle OS-Lifecycle-Events als Konstanten statt Plain-Strings

EVENT_BOOT_INIT = "boot.init"
EVENT_KERNEL_INITIALIZED = "kernel.initialized"
EVENT_PLUGINS_INITIALIZED = "plugins.initialized"
EVENT_RUNTIME_INITIALIZED = "runtime.initialized"
EVENT_RUNTIME_SKIPPED = "runtime.skipped"

DEBUG_MKC_PARSE_START = "DEBUG_MKC_PARSE_START"
DEBUG_MKC_CLASSIFY = "DEBUG_MKC_CLASSIFY"
DEBUG_MKC_EXTRACT = "DEBUG_MKC_EXTRACT"
DEBUG_MCXF_BUILD = "DEBUG_MCXF_BUILD"
DEBUG_RAG_INJECTION = "DEBUG_RAG_INJECTION"
DEBUG_BRIDGE_EXECUTION = "DEBUG_BRIDGE_EXECUTION"
DEBUG_MEL_TOOL_CALL = "DEBUG_MEL_TOOL_CALL"
DEBUG_MEMORY_STORE = "DEBUG_MEMORY_STORE"
DEBUG_CONFLICT_DETECTED = "DEBUG_CONFLICT_DETECTED"


# ── Core Dataclasses ─────────────────────────────────────────────────

@dataclass
class KnowledgeTriple:
    section: str
    subject: str
    predicate: str
    object: str
    confidence: float = 1.0
    turn: int = 0
    source_role: str = "user"


@dataclass
class ConflictRecord:
    subject: str
    statement_a: str
    statement_b: str
    conflict_type: str
    severity: float
    resolution: str = ""


@dataclass
class ToolMatch:
    name: str
    args: dict


@dataclass
class Unmapped:
    original_task: str
    reason: str


@dataclass
class ExecutionPlan:
    intent: str
    steps: List[dict]


@dataclass
class ValidationResult:
    valid: bool
    errors: List[str] = field(default_factory=list)


@dataclass
class FailurePattern:
    pattern_type: str
    tool: str
    task_text: str
    count: int
    description: str


@dataclass
class SemanticGap:
    gap_type: str
    section: str
    content: str
    suggestion: str


@dataclass
class FeedbackReport:
    failure_patterns: List[FailurePattern] = field(default_factory=list)
    semantic_gaps: List[SemanticGap] = field(default_factory=list)
    confidence_adjustments: Dict[str, float] = field(default_factory=dict)
    recommended_mkc_updates: List[str] = field(default_factory=list)
    summary: str = ""


@dataclass
class KernelResult:
    mcxf: 'MCXFDocument'
    execution: list
    memory_id: int
    feedback: FeedbackReport
    success: bool
    errors: List[str] = field(default_factory=list)
    execution_plan: Optional[ExecutionPlan] = None
    execution_id: str = ""


# ── Graph Dataclasses ────────────────────────────────────────────────

@dataclass
class Node:
    id: str
    type: str
    payload: dict
    timestamp: float
    confidence: float = 1.0
    status: str = "created"
    execution_id: str = ""


@dataclass
class Edge:
    source_id: str
    target_id: str
    edge_type: str
    payload: dict = field(default_factory=dict)


# ── Legacy Type Aliases ──────────────────────────────────────────────

ExecutionStep = Dict
PlanDict = Dict[str, Any]


MCXF_REQUIRED_KEYS = ["decisions", "tasks", "architecture", "constraints", "open_questions"]

MCXF_TRIPLE_KEYS = ["section", "subject", "predicate", "object"]


def validate_mcxf(d: dict) -> tuple:
    errors = []
    for key in MCXF_REQUIRED_KEYS:
        if key not in d:
            errors.append(f"Missing MCXF key: '{key}'")
            continue
        if not isinstance(d[key], list):
            errors.append(f"MCXF '{key}' must be a list, got {type(d[key]).__name__}")
    for key in ["decisions", "tasks", "architecture", "constraints"]:
        for i, item in enumerate(d.get(key, [])):
            if not isinstance(item, dict):
                errors.append(f"MCXF '{key}[{i}]' must be a dict")
                continue
            for tk in MCXF_TRIPLE_KEYS:
                if tk not in item:
                    errors.append(f"MCXF '{key}[{i}]' missing '{tk}'")
    for i, q in enumerate(d.get("open_questions", [])):
        if not isinstance(q, str):
            errors.append(f"MCXF 'open_questions[{i}]' must be a string")
    return len(errors) == 0, errors


def detect_old_format(data: dict) -> bool:
    return "intent" in data or "steps" in data


def migrate_to_mcxf(data: dict) -> dict:
    mcxf = {"decisions": [], "tasks": [], "architecture": [], "constraints": [], "open_questions": []}
    if "intent" in data:
        mcxf["decisions"].append({
            "section": "01_DECISIONS", "subject": "user",
            "predicate": "intended", "object": str(data["intent"]),
            "confidence": 1.0
        })
    for step in data.get("steps", []):
        mcxf["tasks"].append({
            "section": "06_TASKS", "subject": "system",
            "predicate": step.get("tool", ""),
            "object": str(step.get("args", {})),
            "confidence": 0.8
        })
    return mcxf


class MCXFDocument:
    def __init__(self):
        self.identity: dict = {}
        self.summary: List[str] = []
        self.decisions: List[KnowledgeTriple] = []
        self.architecture: List[KnowledgeTriple] = []
        self.glossary: List[KnowledgeTriple] = []
        self.constraints: List[KnowledgeTriple] = []
        self.tasks: List[KnowledgeTriple] = []
        self.conflicts: List[ConflictRecord] = []
        self.open_questions: List[str] = []
        self.execution_model: dict = {}
        self.tool_schema: dict = {}
        self.rag_spec: dict = {}
        self.conflict_model: dict = {}
        self.compiler_spec: dict = {}


def _triple_from_dict(t: dict) -> KnowledgeTriple:
    return KnowledgeTriple(
        section=t.get("section", ""),
        subject=t.get("subject", ""),
        predicate=t.get("predicate", ""),
        object=t.get("object", ""),
        confidence=t.get("confidence", 1.0),
        turn=t.get("turn", 0),
        source_role=t.get("source_role", "user"),
    )


def dict_to_mcxf_document(d: dict, input_text: str = "") -> MCXFDocument:
    mcxf = MCXFDocument()
    mcxf.identity = {"source": "muscal_kernel", "input": input_text}
    for t in d.get("decisions", []):
        mcxf.decisions.append(_triple_from_dict(t))
    for t in d.get("tasks", []):
        mcxf.tasks.append(_triple_from_dict(t))
    for t in d.get("architecture", []):
        mcxf.architecture.append(_triple_from_dict(t))
    for t in d.get("constraints", []):
        mcxf.constraints.append(_triple_from_dict(t))
    mcxf.open_questions = list(d.get("open_questions", []))
    return mcxf
