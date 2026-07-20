import builtins
import os as _real_os

# Sandbox reactivated without RestrictedPython.
# Uses namespace isolation + import whitelist + resource watchdog.
# See spec/OVERRIDE.md for history (OVERRIDE-034, OVERRIDE-038).

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


class PluginSandboxError(Exception):
    pass


class PluginSandbox:
    def __init__(self, max_execution_ms=5000):
        self.watchdog = ResourceWatchdog(max_cpu_ms=max_execution_ms)

    def exec_module(self, source, filename="<plugin>"):
        safe_builtins = {
            k: v for k, v in builtins.__dict__.items()
            if k not in ('exec', 'eval', 'compile', '__import__',
                         'open', 'os', 'sys', 'subprocess',
                         'socket', 'ctypes', 'importlib',
                         'getattr', 'setattr', 'delattr')
        }
        safe_builtins['__import__'] = _sandbox_import
        safe_builtins['__build_class__'] = builtins.__dict__['__build_class__']

        namespace = {
            "__builtins__": safe_builtins,
            "__name__": "__plugin__",
            "open": _sandboxed_open,
            "os": _RestrictedOS(),
        }

        self.watchdog.start()
        try:
            code = compile(source, filename, "exec")
            exec(code, namespace)
        except TimeoutExpired:
            raise PluginSandboxError("Plugin exceeded CPU time limit")
        finally:
            self.watchdog.stop()

        return namespace
