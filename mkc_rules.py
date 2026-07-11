import threading

SIGNAL_RULES = {
    "DECISIONS": {
        "keywords": ["we will", "must", "shall", "is defined as", "adopted", "selected"],
        "base_confidence": 0.9,
        "adjustment": 0.0,
    },
    "TASKS": {
        "keywords": ["we build", "implement", "create", "add", "develop"],
        "base_confidence": 0.8,
        "adjustment": 0.0,
    },
    "ARCHITECTURE": {
        "keywords": ["separate", "distinct", "split", "responsibility of", "pipeline"],
        "base_confidence": 0.7,
        "adjustment": 0.0,
    },
    "CONSTRAINTS": {
        "keywords": ["only", "never", "cannot", "must not", "requires"],
        "base_confidence": 0.8,
        "adjustment": 0.0,
    },
    "GLOSSARY": {
        "keywords": ["is a", "means", "called", "defined as", "refers to"],
        "base_confidence": 0.9,
        "adjustment": 0.0,
    },
}

DEFAULT_KEYWORDS = {s: list(r["keywords"]) for s, r in SIGNAL_RULES.items()}

IGNORED_KEYWORDS = ["should", "could", "might", "consider"]

SECTION_FALLBACK = "TASKS"

CONFIDENCE_RANGE = {"min": -0.3, "max": 0.1}
CONFIDENCE_THRESHOLD = 0.5
CONSECUTIVE_FAILURES_RESET = 3
MAX_KEYWORD_ADDITIONS = 5

_lock = threading.RLock()
_tool_failure_history: list = []
_keyword_additions_count: int = 0


_KEYWORD_MAP = None


def _build_keyword_map():
    global _KEYWORD_MAP
    if _KEYWORD_MAP is None:
        mapping = []
        for section, rules in SIGNAL_RULES.items():
            for keyword in rules["keywords"]:
                mapping.append((keyword, section, rules))
        _KEYWORD_MAP = mapping
    return _KEYWORD_MAP


def classify_statement(text: str) -> dict:
    text_lower = text.lower()

    for word in IGNORED_KEYWORDS:
        if word in text_lower:
            return {"section": None, "confidence": 0.0, "reason": "ignored_suggestion"}

    best_section = SECTION_FALLBACK
    best_confidence = 0.0

    with _lock:
        for keyword, section, rules in _build_keyword_map():
            if keyword in text_lower:
                adjusted = rules["base_confidence"] + rules["adjustment"]
                adjusted = max(adjusted, 0.0)
                if adjusted > best_confidence:
                    best_confidence = adjusted
                    best_section = section

        if best_section == SECTION_FALLBACK and best_confidence == 0.0:
            best_confidence = SIGNAL_RULES["TASKS"]["base_confidence"] + SIGNAL_RULES["TASKS"]["adjustment"]

    return {
        "section": best_section,
        "confidence": round(best_confidence, 2),
        "reason": "matched" if best_section != SECTION_FALLBACK else "fallback"
    }


def extract_tool(text: str) -> dict:
    text_lower = text.lower()
    from bridge import _match_console_print, _match_filesystem_write, _match_math_add

    for matcher in [_match_filesystem_write, _match_math_add, _match_console_print]:
        match = matcher(text_lower)
        if match is not None:
            return {"tool": match.name, "args": match.args, "confidence": 0.9}

    return {"tool": None, "args": {}, "confidence": 0.0}


def apply_feedback(report) -> None:
    global _keyword_additions_count, _KEYWORD_MAP

    with _lock:
        _KEYWORD_MAP = None
        for section, delta in report.confidence_adjustments.items():
            if section in SIGNAL_RULES:
                old = SIGNAL_RULES[section]["adjustment"]
                adj_min = CONFIDENCE_RANGE["min"]
                adj_max = CONFIDENCE_RANGE["max"]
                SIGNAL_RULES[section]["adjustment"] = round(max(adj_min, min(adj_max, old + delta)), 2)

        for gap in report.semantic_gaps:
            if _keyword_additions_count >= MAX_KEYWORD_ADDITIONS:
                continue

            if gap.gap_type == "AMBIGUOUS_TASK" and gap.section in SIGNAL_RULES:
                words = gap.content.split()
                for word in words:
                    word = word.strip(".,!?").lower()
                    if len(word) > 2 and word not in SIGNAL_RULES[gap.section]["keywords"]:
                        SIGNAL_RULES[gap.section]["keywords"].append(word)
                        _keyword_additions_count += 1
                        break

        if report.failure_patterns:
            _tool_failure_history.append(len(report.failure_patterns))
            if len(_tool_failure_history) > 100:
                _tool_failure_history.pop(0)

            recent = _tool_failure_history[-CONSECUTIVE_FAILURES_RESET:]
            if len(recent) == CONSECUTIVE_FAILURES_RESET and all(c > 0 for c in recent):
                for section in SIGNAL_RULES:
                    SIGNAL_RULES[section]["adjustment"] = round(
                        SIGNAL_RULES[section]["adjustment"] - 0.05, 2
                    )


def get_effective_confidence(section: str) -> float:
    with _lock:
        rules = SIGNAL_RULES.get(section)
        if not rules:
            return 0.0
        return round(max(0.0, rules["base_confidence"] + rules["adjustment"]), 2)


def get_signal_rules_snapshot() -> dict:
    with _lock:
        return {
            s: {
                "keywords": list(r["keywords"]),
                "base_confidence": r["base_confidence"],
                "adjustment": r["adjustment"]
            }
            for s, r in SIGNAL_RULES.items()
        }


def reset_state():
    global _tool_failure_history, _keyword_additions_count, _KEYWORD_MAP
    with _lock:
        _KEYWORD_MAP = None
        _tool_failure_history = []
        _keyword_additions_count = 0
        for section in SIGNAL_RULES:
            SIGNAL_RULES[section]["adjustment"] = 0.0
            SIGNAL_RULES[section]["keywords"] = DEFAULT_KEYWORDS[section][:]
