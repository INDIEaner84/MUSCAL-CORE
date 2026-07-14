import builtins
import os as _real_os

# RestrictedPython DISABLED per OVERRIDE-038.
# See spec/OVERRIDE.md for history and reactivation instructions.

from features.sandbox.resource_watchdog import ResourceWatchdog, TimeoutExpired


ALLOWED_IMPORTS = frozenset({
    'json', 'time', 'math', 're', 'typing',
    'collections', 'datetime', 'uuid',
})

STORAGE_PATH = _real_os.path.abspath("storage")


class _RestrictedOS:
    def makedirs(self, path, mode=0o777, exist_ok=False):
        abspath = _real_os.path.abspath(path)
        if not abspath.startswith(STORAGE_PATH):
            raise PermissionError(f"Plugin directory creation blocked: {path}")
        _real_os.makedirs(path, mode, exist_ok)

    @property
    def path(self):
        return _real_os.path


def _sandboxed_open(path, mode='r', *args, **kwargs):
    abspath = _real_os.path.abspath(path)
    allowed = STORAGE_PATH
    if not abspath.startswith(allowed):
        raise PermissionError(f"Plugin file access blocked: {path}")
    if 'w' in mode or 'a' in mode:
        _real_os.makedirs(_real_os.path.dirname(abspath), exist_ok=True)
    return builtins.open(path, mode, *args, **kwargs)


def _sandbox_import(name, globals=None, locals=None, fromlist=(), level=0):
    if level == 0 and name not in ALLOWED_IMPORTS:
        raise ImportError(f"Plugin import blocked: {name}")
    return builtins.__import__(name, globals, locals, fromlist, level)


# DEPRECATED: _SANDBOX_GLOBALS preserved for reference only.
# Was populated from RestrictedPython globals. No longer active.
_SANDBOX_GLOBALS = {}


class PluginSandboxError(Exception):
    pass


class PluginSandbox:
    def __init__(self, max_execution_ms=5000):
        self.watchdog = ResourceWatchdog(max_cpu_ms=max_execution_ms)

    def exec_module(self, source, filename="<plugin>"):
        raise PluginSandboxError(
            "Sandbox disabled per OVERRIDE-038. "
            "Use validate_plugin() workflow."
        )
