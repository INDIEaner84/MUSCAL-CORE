import re

from schema import ExecutionPlan, ToolMatch, Unmapped, ValidationResult
from tools import TOOL_REGISTRY, TOOL_SCHEMAS


def _match_filesystem_write(text):
    m = re.search(r"write (?:file )?(\S+)(?: with content (.+))?$", text)
    if m:
        return ToolMatch("filesystem.write", {"path": m.group(1), "content": m.group(2) or ""})

    m = re.search(r"create (?:file )?(\S+)$", text)
    if m:
        return ToolMatch("filesystem.write", {"path": m.group(1), "content": ""})

    return None


def _match_math_add(text):
    m = re.search(r"add (\d+)(?: and | \+ )(\d+)", text)
    if m:
        return ToolMatch("math.add", {"a": int(m.group(1)), "b": int(m.group(2))})

    m = re.search(r"(\d+) \+ (\d+)", text)
    if m:
        return ToolMatch("math.add", {"a": int(m.group(1)), "b": int(m.group(2))})

    return None


def _match_console_print(text):
    m = re.search(r"^print (.+)", text)
    if m:
        return ToolMatch("console.print", {"message": m.group(1)})
    return None


def _match_browser_open(text):
    m = re.search(r"open (?:url )?(https?://\S+)", text)
    if m:
        return ToolMatch("browser.open", {"url": m.group(1)})
    m = re.search(r"go to (https?://\S+)", text)
    if m:
        return ToolMatch("browser.open", {"url": m.group(1)})
    m = re.search(r"navigate to (https?://\S+)", text)
    if m:
        return ToolMatch("browser.open", {"url": m.group(1)})
    return None


def _match_browser_click(text):
    m = re.search(r"click (?:on )?[\"']?([^\"']+)[\"']? (?:in|on) (?:the )?browser", text)
    if m:
        return ToolMatch("browser.click", {"selector": m.group(1).strip()})
    return None


def _match_browser_type(text):
    m = re.search(r"type [\"']([^\"']+)[\"'] into [\"']([^\"']+)[\"']", text)
    if m:
        return ToolMatch("browser.type", {"selector": m.group(2), "text": m.group(1)})
    m = re.search(r"enter [\"']([^\"']+)[\"'] in [\"']([^\"']+)[\"']", text)
    if m:
        return ToolMatch("browser.type", {"selector": m.group(2), "text": m.group(1)})
    return None


def _match_browser_extract(text):
    m = re.search(r"extract text (?:from )?[\"']?([^\"']+)[\"']?", text)
    if m:
        return ToolMatch("browser.extract_text", {"selector": m.group(1).strip()})
    m = re.search(r"get text (?:from )?[\"']?([^\"']+)[\"']?", text)
    if m:
        return ToolMatch("browser.extract_text", {"selector": m.group(1).strip()})
    m = re.search(r"read [\"']?([^\"']+)[\"']?", text)
    if m:
        return ToolMatch("browser.extract_text", {"selector": m.group(1).strip()})
    return None


def _match_browser_screenshot(text):
    if re.search(r"take (a )?screenshot", text):
        m = re.search(r"save (?:to |as )?(\S+)", text)
        path = m.group(1) if m else "screenshot.png"
        return ToolMatch("browser.screenshot", {"path": path})
    return None


def _match_desktop_screenshot(text):
    if re.search(r"take (a )?desktop screenshot", text):
        m = re.search(r"save (?:to |as )?(\S+)", text)
        path = m.group(1) if m else "desktop.png"
        return ToolMatch("desktop.screenshot", {"path": path})
    return None


MATCHERS = [
    _match_browser_open,
    _match_browser_click,
    _match_browser_type,
    _match_browser_extract,
    _match_browser_screenshot,
    _match_desktop_screenshot,
    _match_filesystem_write,
    _match_math_add,
    _match_console_print,
]


def match_tool(triple):
    text = f"{triple.predicate} {triple.object}".strip()

    for matcher in MATCHERS:
        result = matcher(text)
        if result is not None:
            return result

    return Unmapped(
        original_task=text,
        reason="No deterministic match found"
    )


def map_tasks(triples, intent=""):
    steps = []

    for triple in triples:
        match = match_tool(triple)
        if isinstance(match, ToolMatch):
            steps.append({"tool": match.name, "args": match.args})
        else:
            steps.append({
                "tool": "UNMAPPED",
                "original_task": match.original_task,
                "reason": match.reason
            })

    return ExecutionPlan(intent=intent, steps=steps)


def validate_plan(plan):
    errors = []

    if not plan.steps:
        errors.append("ExecutionPlan has no steps")

    for i, step in enumerate(plan.steps):
        tool_name = step.get("tool", "")
        if tool_name == "UNMAPPED":
            continue

        if tool_name not in TOOL_REGISTRY and not (tool_name.startswith("browser.") or tool_name.startswith("desktop.")):
            errors.append(f"Step {i}: Unknown tool '{tool_name}'")
            continue

        schema = TOOL_SCHEMAS.get(tool_name)
        if schema is None:
            continue

        args = step.get("args", {})
        for param, expected_type in schema["input"].items():
            if param not in args:
                errors.append(f"Step {i}: Missing arg '{param}' for {tool_name}")
                continue
            if not isinstance(args[param], expected_type):
                errors.append(
                    f"Step {i}: Arg '{param}' expected {expected_type.__name__}, got {type(args[param]).__name__}"
                )

    return ValidationResult(valid=len(errors) == 0, errors=errors)
