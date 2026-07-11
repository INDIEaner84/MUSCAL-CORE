def test_no_import_in_kernel():
    import kernel
    kernel_src = open(kernel.__file__).read() if hasattr(kernel, "__file__") else ""
    assert "__import__(" not in kernel_src
    assert "import time" in kernel_src


def test_no_import_in_database():
    from runtime import database
    db_src = open(database.__file__).read() if hasattr(database, "__file__") else ""
    assert "__import__(" not in db_src
    assert "import datetime" in db_src


def test_rag_retrieve():
    import memory
    memory._conn = None
    memory.init()
    memory.store_snapshot("test alpha beta gamma", {"k": "v1"}, {"ok": True})
    memory.store_snapshot("hello world test", {"k": "v2"}, {"ok": True})
    from rag import retrieve as rag_retrieve
    results_default = rag_retrieve("alpha gamma", top_k=3)
    assert len(results_default) >= 1
    assert any("alpha" in r["input_text"] or "gamma" in r["input_text"] for r in results_default)


def test_admin_whitelist():
    from runtime.api.admin import _ALLOWED_COMMANDS, _ALLOWED_URL_PREFIXES
    assert len(_ALLOWED_COMMANDS) > 0
    assert len(_ALLOWED_URL_PREFIXES) > 0


def test_plugin_loader_regex():
    import plugin_loader
    assert len(plugin_loader.FORBIDDEN_REGEX) > 0
    assert any("__import__" in r.pattern for r in plugin_loader.FORBIDDEN_REGEX)
    assert any("subprocess" in r.pattern for r in plugin_loader.FORBIDDEN_REGEX)


def test_muscal_loop_allowlist():
    import muscal_loop
    assert callable(muscal_loop._exec_opencode_run)
    loop_src = open(muscal_loop.__file__).read() if hasattr(muscal_loop, "__file__") else ""
    assert "shlex.split" in loop_src
    assert "stripped.startswith" in loop_src
