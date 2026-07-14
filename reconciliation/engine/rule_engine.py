from __future__ import annotations

from reconciliation.core.context import ScanContext
from reconciliation.core.finding import FindingSet
from reconciliation.core.rule import Rule, RuleSet
from reconciliation.engine.checkers import (
    ContentMatchChecker,
    FileCountChecker,
    FileExistsChecker,
    RuleChecker,
)


class RuleEngine:
    def __init__(self) -> None:
        self._checkers: list[RuleChecker] = []

    @property
    def checkers(self) -> list[RuleChecker]:
        return list(self._checkers)

    def register_checker(self, checker: RuleChecker) -> None:
        self._checkers.append(checker)

    @classmethod
    def default(cls) -> RuleEngine:
        engine = cls()
        engine.register_checker(FileExistsChecker())
        engine.register_checker(ContentMatchChecker())
        engine.register_checker(FileCountChecker())
        return engine

    def validate(
        self,
        rule: Rule,
        target: object,
        context: ScanContext,
    ) -> Finding | None:
        for checker in self._checkers:
            if checker.supports(rule):
                return checker.check(rule, target, context)
        return None

    def validate_all(
        self,
        ruleset: RuleSet,
        target: object,
        context: ScanContext,
    ) -> FindingSet:
        findings: list = []
        for rule in ruleset.rules:
            result = self.validate(rule, target, context)
            if result is not None:
                findings.append(result)
        return FindingSet(scanner=ruleset.name, findings=findings)
