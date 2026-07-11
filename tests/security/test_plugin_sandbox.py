import os
import tempfile

import pytest


@pytest.fixture
def sandbox():
    from features.sandbox import PluginSandbox
    return PluginSandbox()


BASIC_PLUGIN = """
class Plugin:
    name = "test"
    version = "1.0.0"
    def register(self, hooks):
        self.hooks = hooks
    def execute(self, ctx):
        return {"status": "ok"}
"""


class TestPluginSandbox:
    def test_basic_plugin_execution(self, sandbox):
        result = sandbox.exec_module(BASIC_PLUGIN)
        P = result.get("Plugin")
        assert P is not None
        p = P()
        assert p.name == "test"
        assert p.version == "1.0.0"
        assert p.execute({}) == {"status": "ok"}

    def test_class_inheritance(self, sandbox):
        source = """
class Base:
    version = "1.0"
class Plugin(Base):
    name = "child"
    def register(self, hooks):
        pass
"""
        result = sandbox.exec_module(source)
        P = result.get("Plugin")
        assert P is not None
        p = P()
        assert p.name == "child"
        assert p.version == "1.0"

    def test_blocked_os_import(self, sandbox):
        with pytest.raises(Exception, match="(?i)blocked"):
            sandbox.exec_module('import os\nclass Plugin: pass')

    def test_blocked_sys_import(self, sandbox):
        with pytest.raises(Exception, match="(?i)blocked"):
            sandbox.exec_module('import sys\nclass Plugin: pass')

    def test_blocked_subprocess_import(self, sandbox):
        with pytest.raises(Exception, match="(?i)blocked"):
            sandbox.exec_module('import subprocess\nclass Plugin: pass')

    def test_blocked_socket_import(self, sandbox):
        with pytest.raises(Exception, match="(?i)blocked"):
            sandbox.exec_module('import socket\nclass Plugin: pass')

    def test_blocked_ctypes_import(self, sandbox):
        with pytest.raises(Exception, match="(?i)blocked"):
            sandbox.exec_module('import ctypes\nclass Plugin: pass')

    def test_allowed_json_import(self, sandbox):
        source = 'import json\nclass Plugin:\n    pass'
        result = sandbox.exec_module(source)
        assert "Plugin" in result

    def test_allowed_time_import(self, sandbox):
        source = 'import time\nclass Plugin:\n    pass'
        result = sandbox.exec_module(source)
        assert "Plugin" in result

    def test_allowed_math_import(self, sandbox):
        source = 'import math\nclass Plugin:\n    pass'
        result = sandbox.exec_module(source)
        assert "Plugin" in result

    def test_blocked_eval(self, sandbox):
        with pytest.raises(Exception):
            sandbox.exec_module('eval("1+1")\nclass Plugin: pass')

    def test_blocked_exec(self, sandbox):
        with pytest.raises(Exception):
            sandbox.exec_module('exec("x=1")\nclass Plugin: pass')

    def test_blocked_compile(self, sandbox):
        with pytest.raises(Exception):
            sandbox.exec_module('compile("x=1","","exec")\nclass Plugin: pass')

    def test_storage_write_via_open(self, sandbox):
        source = '''
class Plugin:
    def register(self, hooks):
        with open("storage/test_sandbox_write.txt", "w") as f:
            f.write("ok")
'''
        result = sandbox.exec_module(source)
        P = result.get("Plugin")
        assert P is not None
        p = P()
        p.register({})
        test_file = "storage/test_sandbox_write.txt"
        assert os.path.exists(test_file)
        with open(test_file) as f:
            assert f.read() == "ok"
        os.remove(test_file)

    def test_blocked_outside_storage_write(self, sandbox):
        with tempfile.TemporaryDirectory() as tmpdir:
            source = f'''
class Plugin:
    def register(self, hooks):
        with open("{tmpdir}/bad.txt", "w") as f:
            f.write("nope")
'''
            with pytest.raises(Exception, match="(?i)blocked"):
                result = sandbox.exec_module(source)
                P = result.get("Plugin")
                if P:
                    P().register({})

    def test_os_makedirs_to_storage(self, sandbox):
        source = '''
class Plugin:
    def register(self, hooks):
        os.makedirs("storage/sandbox_test_dir", exist_ok=True)
'''
        result = sandbox.exec_module(source)
        P = result.get("Plugin")
        assert P is not None
        p = P()
        p.register({})
        test_dir = "storage/sandbox_test_dir"
        assert os.path.isdir(test_dir)
        os.rmdir(test_dir)

    def test_missing_plugin_class(self, sandbox):
        source = 'x = 1\ny = 2'
        result = sandbox.exec_module(source)
        assert "Plugin" not in result

    def test_function_plugin(self, sandbox):
        source = '''
def Plugin():
    return {"name": "func"}
'''
        result = sandbox.exec_module(source)
        assert "Plugin" in result
        assert callable(result["Plugin"])
