from __future__ import annotations

from abc import ABC, abstractmethod

from reconciliation.runner import ReconciliationRunner


class HookBase(ABC):
    @abstractmethod
    def run(self, runner: ReconciliationRunner) -> int:
        ...
