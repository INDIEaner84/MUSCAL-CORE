import os

CORE_FILES = frozenset({
    "kernel.py",
    "mkc.py",
    "bridge.py",
    "memory.py",
    "mel.py",
    "schema.py",
    "mkc_rules.py",
    "config.py",
    "event_bus.py",
    "graph.py",
    "feedback.py",
    "muscal_os.py",
    "main.py",
    "main_boot.py",
    "boot_manager.py",
    "os_config.py",
    "plugin_registry.py",
    "plugin_loader.py",
    "sphere.py",
    "debugger.py",
    "tools.py",
    "rag.py",
    "trace_engine.py",
    "cognitive_diff.py",
    "kernel_diff_engine.py",
    "muscal_loop.py",
    "loop_controller.py",
    "compiler_state.py",
    "compiler_updater.py",
    "compiler_validator.py",
    "compiler_version.py",
    "chat_compiler.py",
    "api_server.py",
    "dashboard.py",
    "system_runtime.py",
})

CORE_DIRS = frozenset({
    "runtime/kernel",
    "runtime/llm",
    "runtime/optimizer",
    "runtime/api",
    "runtime/services",
    "runtime/observation",
    "guards",
    "spec",
})

ALLOWED_WRITE_DIRS = frozenset({
    "features",
    "storage",
    "tests",
    "docs",
})


def validate_write(path: str):
    abs_path = os.path.abspath(path)
    filename = os.path.basename(abs_path)
    rel_dir = os.path.relpath(os.path.dirname(abs_path))

    if filename in CORE_FILES:
        raise PermissionError(
            f"ARCHITECTURE VIOLATION\n\n"
            f"Attempted write to protected core file:\n"
            f"  {path}\n\n"
            f"CORE IS IMMUTABLE.\n"
            f"Extensions must go in /features/.\n"
            f"See spec/IMMUTABILITY_CONTRACT.md"
        )

    for core_dir in CORE_DIRS:
        if rel_dir.startswith(core_dir) or core_dir.startswith(rel_dir):
            raise PermissionError(
                f"ARCHITECTURE VIOLATION\n\n"
                f"Attempted write to protected core directory:\n"
                f"  {path}\n\n"
                f"CORE IS IMMUTABLE.\n"
                f"Extensions must go in /features/."
            )


def is_core_file(path: str) -> bool:
    filename = os.path.basename(path)
    if filename in CORE_FILES:
        return True
    rel_dir = os.path.relpath(os.path.dirname(os.path.abspath(path)))
    for core_dir in CORE_DIRS:
        if rel_dir.startswith(core_dir) or core_dir.startswith(rel_dir):
            return True
    return False
