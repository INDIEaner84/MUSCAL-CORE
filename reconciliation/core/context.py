from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from reconciliation.core.scope import ScanScope
from reconciliation.snapshot.repository_snapshot import RepositorySnapshot


@dataclass(frozen=True)
class ScanContext:
    snapshot: RepositorySnapshot | None = None
    scope: ScanScope | None = None
    config: dict[str, Any] = field(default_factory=dict)
