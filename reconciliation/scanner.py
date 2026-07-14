from __future__ import annotations

from abc import ABC, abstractmethod

from reconciliation.core.context import ScanContext
from reconciliation.core.finding import FindingSet
from reconciliation.core.rule import Rule
from reconciliation.core.scope import ScanScope


class ScannerBase(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def rules(self) -> list[Rule]: ...

    @abstractmethod
    def scan(self, context: ScanContext) -> FindingSet: ...

    def scan_legacy(self, scope: ScanScope) -> FindingSet:
        return self.scan(ScanContext(scope=scope))

    @property
    def auto_fixable(self) -> bool:
        return False
