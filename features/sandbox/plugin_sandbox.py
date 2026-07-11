import builtins
import os as _real_os

from RestrictedPython import compile_restricted, safe_globals, limited_builtins, utility_builtins
from RestrictedPython.Guards import guarded_setattr, guarded_delattr

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


_SANDBOX_GLOBALS = dict(safe_globals)
_SANDBOX_GLOBALS.update(limited_builtins)
_SANDBOX_GLOBALS.update(utility_builtins)

_SANDBOX_GLOBALS['__builtins__'] = dict(_SANDBOX_GLOBALS['__builtins__'])
_SANDBOX_GLOBALS['__builtins__']['__import__'] = _sandbox_import
_SANDBOX_GLOBALS['__builtins__']['open'] = _sandboxed_open
_SANDBOX_GLOBALS['__builtins__']['_write_'] = lambda ob: ob
_SANDBOX_GLOBALS['os'] = _RestrictedOS()
_SANDBOX_GLOBALS['__metaclass__'] = type
_SANDBOX_GLOBALS['__name__'] = '__main__'

for mod_name in ALLOWED_IMPORTS:
    try:
        _SANDBOX_GLOBALS[mod_name] = __import__(mod_name)
    except ImportError:
        pass


class PluginSandboxError(Exception):
    pass


class PluginSandbox:
    def __init__(self, max_execution_ms=5000):
        self.watchdog = ResourceWatchdog(max_cpu_ms=max_execution_ms)

    def exec_module(self, source, filename="<plugin>"):
        bytecode = compile_restricted(source, filename=filename, mode="exec")
        sandbox = dict(_SANDBOX_GLOBALS)
        try:
            self.watchdog.start()
            exec(bytecode, sandbox)
        except TimeoutExpired:
            raise
        except Exception as e:
            raise PluginSandboxError(f"Sandbox execution failed: {e}") from e
        finally:
            self.watchdog.cancel()
        return sandbox
