"""
MUSCAL File System API (Rule-5-konform: deterministisch, kein LLM, kein GPU)
"""

import json
from datetime import datetime, timezone
from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent.parent.resolve()
_USER_DIR = _PROJECT_ROOT / "user"


def _ensure_user_dir() -> Path:
    _USER_DIR.mkdir(parents=True, exist_ok=True)
    return _USER_DIR


def safe_path(requested: str) -> Path | None:
    path = (_PROJECT_ROOT / requested.lstrip("/")).resolve()
    user_dir = _ensure_user_dir()
    kernel_docs = _PROJECT_ROOT / "kernel" / "docs"
    allowed = [user_dir, kernel_docs, _PROJECT_ROOT]
    if not any(str(path).startswith(str(a)) for a in allowed):
        return None
    if not path.exists():
        return None
    return path


def list_dir(dir_path: str) -> dict:
    path = safe_path(dir_path)
    if path is None:
        return {"error": "Access denied"}, 403
    if not path.is_dir():
        return {"error": "Not found"}, 404
    entries = []
    for child in sorted(path.iterdir()):
        is_dir = child.is_dir()
        stat = child.stat()
        entries.append({
            "name": child.name,
            "type": "dir" if is_dir else "file",
            "path": str(child.relative_to(_PROJECT_ROOT)),
            "size": stat.st_size if not is_dir else 0,
            "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        })
    return {"entries": entries, "path": dir_path}, 200


def read_file(file_path: str) -> dict:
    resolved = safe_path(file_path)
    if resolved is None or resolved.is_dir():
        return {"error": "Not found"}, 404
    try:
        content = resolved.read_text("utf-8")
        return {
            "path": str(resolved.relative_to(_PROJECT_ROOT)),
            "content": content,
            "size": resolved.stat().st_size,
        }, 200
    except Exception as e:
        return {"error": str(e)}, 500


def write_file(file_path: str, content: str) -> dict:
    resolved = (_PROJECT_ROOT / file_path.lstrip("/")).resolve()
    user_dir = _ensure_user_dir()
    if not str(resolved).startswith(str(user_dir)):
        return {"error": "Write restricted to user/ directory"}, 403
    try:
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(content, "utf-8")
        return {"status": "ok", "path": str(resolved.relative_to(_PROJECT_ROOT))}, 200
    except Exception as e:
        return {"error": str(e)}, 500


def delete_file(file_path: str) -> dict:
    resolved = (_PROJECT_ROOT / file_path.lstrip("/")).resolve()
    user_dir = _ensure_user_dir()
    if not str(resolved).startswith(str(user_dir)):
        return {"error": "Delete restricted to user/ directory"}, 403
    if not resolved.exists():
        return {"error": "Not found"}, 404
    try:
        if resolved.is_dir():
            resolved.rmdir()
        else:
            resolved.unlink()
        return {"status": "ok", "path": str(resolved.relative_to(_PROJECT_ROOT))}, 200
    except Exception as e:
        return {"error": str(e)}, 500
