from typing import Any, Dict, List, Optional


def validate_json(body: dict, fields: Dict[str, type]) -> Optional[str]:
    for name, expected_type in fields.items():
        if name not in body:
            return f"missing required field: {name}"
        val = body[name]
        if expected_type is list and not isinstance(val, list):
            return f"field '{name}' must be a list"
        if expected_type is dict and not isinstance(val, dict):
            return f"field '{name}' must be an object"
        if expected_type is str and not isinstance(val, str):
            return f"field '{name}' must be a string"
        if expected_type is int and not isinstance(val, (int, float)):
            return f"field '{name}' must be a number"
    return None


def validate_query(params: dict, fields: Dict[str, type]) -> Optional[str]:
    for name, expected_type in fields.items():
        val = params.get(name)
        if val is None:
            continue
        if expected_type is int:
            try:
                int(val)
            except (ValueError, TypeError):
                return f"query parameter '{name}' must be an integer"
    return None
