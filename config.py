import os
from datetime import datetime, timezone
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).parent

_session_id = None


def get_session_id():
    global _session_id
    if _session_id is None:
        _session_id = datetime.now(timezone.utc).strftime("session_%Y%m%d_%H%M%S")
    return _session_id


SESSION_ID          = get_session_id()
DB_PATH             = Path(os.environ.get("MUSCAL_DB_PATH", str(BASE_DIR / "storage" / "muscal.db")))
SNAPSHOT_THRESHOLD  = int(os.environ.get("MUSCAL_SNAPSHOT_THRESHOLD", "10000"))

OLLAMA_BASE   = os.environ.get("OLLAMA_BASE", "http://localhost:11434")
QWEN_MODEL    = os.environ.get("QWEN_MODEL", "qwen2.5:1.5b")
R1_MODEL      = os.environ.get("R1_MODEL", "deepseek-r1:8b")
R1_KEEP_ALIVE = int(os.environ.get("R1_KEEP_ALIVE", "300"))
SMOL_MODEL    = os.environ.get("SMOL_MODEL", "qwen2.5:1.5b")

OBSERVATION_INTERVAL = float(os.environ.get("OBSERVATION_INTERVAL", "5.0"))
WRITER_TIMEOUT       = float(os.environ.get("WRITER_TIMEOUT", "5.0"))

RUNTIME_FLASK_PORT = int(os.environ.get("RUNTIME_FLASK_PORT", "5001"))
