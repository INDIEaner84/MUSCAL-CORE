# write_guard.py

import os

BLOCKED_PATHS = [
    "/core/",
    "/kernel/",
    "/runtime/core/",
    "/architecture/"
]

def validate_write(path: str):
    for blocked in BLOCKED_PATHS:
        if blocked in path:
            raise Exception(f"""
ARCHITECTURE VIOLATION

Attempted write to protected area:
{path}

CORE IS IMMUTABLE.
Use /features instead.
""")
