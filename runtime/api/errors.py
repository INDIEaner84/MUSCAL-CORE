from typing import Any, Dict, Tuple


def api_error(message: str, status: int = 500) -> Tuple[Dict[str, Any], int]:
    return {"error": message}, status


def api_status_error(detail: str, status: int = 400) -> Tuple[Dict[str, Any], int]:
    return {"status": "error", "detail": detail}, status
