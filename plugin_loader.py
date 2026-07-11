import importlib
import inspect
import os
import sys

import config
from plugin_registry import HOOKS, PLUGINS, add_health_listener

FEATURES_DIR = os.path.join(os.path.dirname(__file__), "features")

import re as _re

FORBIDDEN_PATTERNS = [
    "sqlite3.connect",
    "import kernel",
    "from kernel import",
    "import muscal_os",
    "from muscal_os import",
    "import main_boot",
    "from main_boot import",
    "import config",
    "from config import",
    "import memory",
    "from memory import",
    "import plugin_registry",
    "from plugin_registry import",
    "import mkc",
    "from mkc import",
    "import bridge",
    "from bridge import",
    "import mel",
    "from mel import",
    "import schema",
    "from schema import",
    "import event_bus",
    "from event_bus import",
    "import graph",
    "from graph import",
    "import feedback",
    "from feedback import",
    "import main",
    "from main import",
    "import boot_manager",
    "from boot_manager import",
    "import os_config",
    "from os_config import",
    "import sphere",
    "from sphere import",
    "import debugger",
    "from debugger import",
    "import tools",
    "from tools import",
    "import rag",
    "from rag import",
    "import trace_engine",
    "from trace_engine import",
    "MuscalKernel",
    "SystemAgentRuntime",
    "global ",
    "__builtins__",
    "ctypes.",
    "import socket",
    "importlib.import_module",
    "importlib.import",
]

FORBIDDEN_REGEX = [
    _re.compile(r"__import__\s*\("),
    _re.compile(r"exec\s*\("),
    _re.compile(r"eval\s*\("),
    _re.compile(r"compile\s*\("),
    _re.compile(r"subprocess\."),
    _re.compile(r"os\.system"),
    _re.compile(r"os\.popen"),
    _re.compile(r"os\.fork"),
    _re.compile(r"__builtins__"),
    _re.compile(r"ctypes\."),
    _re.compile(r"importlib\.import_module"),
]

def validate_plugin(module) -> list[str]:
    try:
        source = inspect.getsource(module) if hasattr(module, "__file__") and module.__file__ else ""
    except (OSError, TypeError):
        source = ""
    violations = []
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in source:
            violations.append(pattern)
    for regex in FORBIDDEN_REGEX:
        if regex.search(source):
            violations.append(regex.pattern)
    return violations


def load_plugins():
    if not os.path.isdir(FEATURES_DIR):
        return

    sys.path.insert(0, os.path.dirname(FEATURES_DIR))

    for root, dirs, files in os.walk(FEATURES_DIR):
        if "sandbox" in dirs:
            dirs.remove("sandbox")
        for file in files:
            if not file.endswith(".py") or file == "__init__.py":
                continue

            rel_path = os.path.relpath(os.path.join(root, file), os.path.dirname(FEATURES_DIR))
            module_path = rel_path.replace(os.sep, ".")[:-3]

            try:
                module = importlib.import_module(module_path)
                if not hasattr(module, "Plugin"):
                    continue
                violations = validate_plugin(module)
                if violations:
                    print(f"PLUGIN SAFETY BLOCKED: {module_path}")
                    print(f"  Forbidden patterns: {violations}")
                    continue
                plugin = module.Plugin()

                if not hasattr(plugin, "name"):
                    plugin.name = module_path.split(".")[-1]
                if not hasattr(plugin, "version"):
                    plugin.version = "0.0.0"

                HOOKS["_session_id"] = getattr(config, "SESSION_ID", "")
                HOOKS["_add_health_listener"] = add_health_listener
                PLUGINS.append(plugin)
                try:
                    plugin.register(HOOKS)
                finally:
                    del HOOKS["_session_id"]
                    del HOOKS["_add_health_listener"]
                ver = getattr(plugin, "version", "0.0.0")
                print(f"PLUGIN LOADED: {plugin.name} v{ver} ({module_path})")

            except Exception as e:
                print(f"PLUGIN LOAD FAILED: {module_path}: {e}")
