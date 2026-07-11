import os

ALLOWED_WRITE_PATHS = [
    os.path.abspath(p) for p in
    ["/tmp", os.path.join(os.path.dirname(__file__), "storage")]
]
MAX_WRITE_SIZE = 1_048_576


def write(path, content):
    abspath = os.path.abspath(path)
    allowed = any(abspath.startswith(base) for base in ALLOWED_WRITE_PATHS)
    if not allowed:
        return {"status": "blocked", "path": path, "error": "path not allowed"}
    if len(content) > MAX_WRITE_SIZE:
        return {"status": "blocked", "path": path, "error": "content exceeds max size"}
    os.makedirs(os.path.dirname(abspath), exist_ok=True)
    with open(abspath, "w") as f:
        f.write(content)
    return {"status": "written", "path": path}


def add(a, b):
    return {"result": a + b}


def print_console(message):
    print(message)
    return {"printed": message}


TOOL_REGISTRY = {
    "filesystem.write": write,
    "math.add": add,
    "console.print": print_console
}


TOOL_SCHEMAS = {
    "filesystem.write": {
        "input": {"path": str, "content": str},
        "output": {"status": str, "path": str},
        "constraints": ["max_size:1048576", "allowed_paths:/tmp/*,./storage/*"]
    },
    "math.add": {
        "input": {"a": (int, float), "b": (int, float)},
        "output": {"result": (int, float)},
        "constraints": ["pure:true", "no_side_effects:true"]
    },
    "console.print": {
        "input": {"message": str},
        "output": {"printed": str},
        "constraints": ["side_effect:stdout", "max_length:4096"]
    },
    "browser.open": {
        "input": {"url": str},
        "output": {"status": str, "title": str, "url": str},
        "constraints": ["timeout:10", "no_javascript_injection"]
    },
    "browser.click": {
        "input": {"selector": str},
        "output": {"status": str},
        "constraints": ["timeout:10", "no_javascript_injection"]
    },
    "browser.type": {
        "input": {"selector": str, "text": str},
        "output": {"status": str},
        "constraints": ["max_length:1000", "timeout:10"]
    },
    "browser.extract_text": {
        "input": {"selector": str},
        "output": {"text": str},
        "constraints": ["max_chars:10000", "timeout:10"]
    },
    "browser.screenshot": {
        "input": {"path": str},
        "output": {"status": str, "path": str},
        "constraints": ["allowed_path:./screenshots/*"]
    },
    "browser.scroll": {
        "input": {"direction": str},
        "output": {"status": str},
        "constraints": ["direction:up|down"]
    },
    "desktop.screenshot": {
        "input": {"path": str},
        "output": {"status": str, "path": str},
        "constraints": ["allowed_path:./screenshots/*"]
    },
    "desktop.type": {
        "input": {"text": str},
        "output": {"status": str},
        "constraints": ["max_length:500", "no_system_combinations"]
    },
    "desktop.click": {
        "input": {"x": (int, float), "y": (int, float)},
        "output": {"status": str},
        "constraints": ["screen_bounds_only"]
    },
    "desktop.open_app": {
        "input": {"name": str},
        "output": {"status": str},
        "constraints": ["allowed_apps:[]"]
    },
    "desktop.move": {
        "input": {"x": (int, float), "y": (int, float)},
        "output": {"status": str},
        "constraints": ["screen_bounds_only"]
    },
    "desktop.keypress": {
        "input": {"key": str},
        "output": {"status": str},
        "constraints": ["no_system_combinations"]
    }
}
