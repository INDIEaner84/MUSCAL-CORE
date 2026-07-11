import json
import re

from mkc_rules import classify_statement, extract_tool
from schema import detect_old_format, migrate_to_mcxf, validate_mcxf

MAX_INPUT_LENGTH = 100_000


def _sanitize_input(text: str) -> str:
    if "\0" in text:
        raise ValueError("null byte in input")
    if len(text) > MAX_INPUT_LENGTH:
        raise ValueError(f"input exceeds max length ({len(text)} > {MAX_INPUT_LENGTH})")
    return text


def _format_task(tool_name: str, tool_args: dict, user_input: str) -> dict:
    if tool_name == "filesystem.write":
        path = tool_args.get("path", "output.txt")
        content = tool_args.get("content", "")
        predicate = "write file"
        obj = f"{path} with content {content}" if content else path
    elif tool_name == "math.add":
        predicate = "add"
        obj = f"{tool_args.get('a', 0)} and {tool_args.get('b', 0)}"
    elif tool_name == "console.print":
        predicate = "print"
        obj = tool_args.get("message", user_input)
    elif tool_name.startswith("browser.") or tool_name.startswith("desktop."):
        predicate = tool_name
        obj = json.dumps(tool_args) if tool_args else user_input
    else:
        predicate = tool_name
        obj = user_input
    return {
        "section": "06_TASKS",
        "subject": "system",
        "predicate": predicate,
        "object": obj,
        "confidence": 0.8,
    }


def mkc(user_input: str, raw_input: str = None) -> dict:
    user_input = _sanitize_input(user_input)
    if raw_input is not None:
        raw_input = _sanitize_input(raw_input)
    else:
        raw_input = user_input

    classification = classify_statement(user_input)
    section = classification.get("section")
    confidence = classification.get("confidence", 0.0)

    mcxf = {
        "decisions": [],
        "tasks": [],
        "architecture": [],
        "constraints": [],
        "open_questions": [],
    }

    if section is None:
        mcxf["open_questions"].append(user_input)
        return mcxf

    mcxf["decisions"].append({
        "section": "01_DECISIONS",
        "subject": "user",
        "predicate": "requested",
        "object": user_input,
        "confidence": confidence,
    })

    tool_info = extract_tool(raw_input)

    if tool_info["tool"] is not None:
        task = _format_task(tool_info["tool"], tool_info["args"], user_input)
        task["confidence"] = tool_info.get("confidence", 0.9)
        mcxf["tasks"].append(task)
    else:
        if "write" in user_input:
            mcxf["tasks"].append(_format_task(
                "filesystem.write",
                {"path": "output.txt", "content": user_input},
                user_input
            ))
        elif re.search(r'\d+.*add|add.*\d+', user_input.lower()):
            nums = [int(s) for s in user_input.split() if s.isdigit()]
            a, b = (nums[0], nums[1]) if len(nums) >= 2 else (2, 3)
            mcxf["tasks"].append(_format_task(
                "math.add",
                {"a": a, "b": b},
                user_input
            ))
        else:
            mcxf["tasks"].append(_format_task(
                "console.print",
                {"message": user_input},
                user_input
            ))

    ok, errs = validate_mcxf(mcxf)
    if not ok:
        raise ValueError(f"MKC produced invalid MCXF: {errs}")
    return mcxf


def ensure_mcxf(data: dict) -> dict:
    if detect_old_format(data):
        return migrate_to_mcxf(data)
    ok, errs = validate_mcxf(data)
    if not ok:
        raise ValueError(f"Invalid MCXF data: {errs}")
    return data
