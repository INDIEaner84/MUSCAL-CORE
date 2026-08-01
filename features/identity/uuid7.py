import os
import re
import time
from typing import Optional

UUID7_VERSION = "1.0.0"

_UUID7_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def uuid7(seconds: Optional[float] = None) -> str:
    """Generate a UUID v7 string using pure Python.

    Layout (128 bits):
      0-47:  Unix timestamp ms (48 bits)
     48-51:  version = 7 (4 bits)
     52-63:  rand_a (12 bits)
     64-65:  variant = 10 (2 bits)
     66-127: rand_b (62 bits)

    Python 3.12 does not have uuid.uuid7() (added in 3.14).
    """
    if seconds is not None:
        timestamp_ms = int(seconds * 1000)
    else:
        timestamp_ms = int(time.time() * 1000)

    ts_bytes = timestamp_ms.to_bytes(6, byteorder="big")
    rand = os.urandom(10)

    b = bytearray(16)
    b[0:6] = ts_bytes
    b[6] = (0x70) | (rand[0] >> 4)
    b[7] = ((rand[0] & 0x0f) << 4) | (rand[1] >> 4)
    b[8] = (0x80) | (rand[1] & 0x0f)
    b[9:16] = rand[2:9]

    h = b.hex()
    return f"{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


def uuid7_bytes(seconds: Optional[float] = None) -> bytes:
    return bytes.fromhex(uuid7(seconds).replace("-", ""))


def is_uuid7(value: str) -> bool:
    return bool(_UUID7_PATTERN.match(value))
