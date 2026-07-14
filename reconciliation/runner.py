from __future__ import annotations

import datetime
import os

from reconciliation.core.context import ScanContext
from reconciliation.core.finding import FindingSet
from reconciliation.core.scope import ScanScope
from reconciliation.report import ReportGenerator
from reconciliation.scanner import ScannerBase
from reconciliation.snapshot.repository_snapshot import RepositorySnapshot


class ReconciliationRunner:
    def __init__(self, repo_root: str = "."):
        self._scanners: dict[str, ScannerBase] = {}
        self.repo_root = os.path.abspath(repo_root)
        self._snapshot: RepositorySnapshot | None = None

    @property
    def scanners(self) -> list[ScannerBase]:
        return list(self._scanners.values())

    def register(self, scanner: ScannerBase) -> None:
        self._scanners[scanner.name] = scanner

    def run_all(
        self,
        context: ScanContext | None = None,
    ) -> list[FindingSet]:
        if context is None:
            context = self._build_context()
        results: list[FindingSet] = []
        for scanner in self._scanners.values():
            results.append(scanner.scan(context))
        return results

    def run_scanner(
        self,
        name: str,
        context: ScanContext | None = None,
    ) -> FindingSet | None:
        scanner = self._scanners.get(name)
        if scanner is None:
            return None
        if context is None:
            context = self._build_context()
        return scanner.scan(context)

    def save_report(
        self,
        results: list[FindingSet],
        path: str,
        checkpoint: str = "",
    ) -> str:
        gen = ReportGenerator()
        report = gen.reconciliation_report(results, checkpoint=checkpoint)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            f.write(report)
        return path

    def _build_context(self) -> ScanContext:
        snapshot = RepositorySnapshot(self.repo_root)
        snapshot.build()
        scope = snapshot.to_scan_scope()
        return ScanContext(snapshot=snapshot, scope=scope)
