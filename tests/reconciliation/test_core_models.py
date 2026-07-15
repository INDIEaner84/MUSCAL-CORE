from reconciliation.core.finding import Category, Finding, FindingSet, FindingStatus, Severity
from reconciliation.core.rule import Rule
from reconciliation.core.scope import ScanScope


class TestCategory:
    def test_values(self):
        assert Category.A.value == "A"
        assert Category.B.value == "B"
        assert Category.C.value == "C"
        assert Category.D.value == "D"

    def test_members(self):
        assert len(Category) == 4


class TestSeverity:
    def test_values(self):
        assert Severity.CRITICAL.value == "Critical"
        assert Severity.HIGH.value == "High"
        assert Severity.MEDIUM.value == "Medium"
        assert Severity.LOW.value == "Low"

    def test_members(self):
        assert len(Severity) == 4


class TestFinding:
    def test_minimal_creation(self):
        f = Finding(
            finding_id="RFC-001_test",
            scanner="rfc_validator",
            file="docs/RFC-001.md",
            severity=Severity.MEDIUM,
            category=Category.B,
        )
        assert f.finding_id == "RFC-001_test"
        assert f.status == FindingStatus.OPEN
        assert f.line is None

    def test_full_creation(self):
        f = Finding(
            finding_id="RFC-003_test",
            scanner="rfc_validator",
            file="docs/RFC-003.md",
            severity=Severity.HIGH,
            category=Category.A,
            status=FindingStatus.DEFERRED,
            line=42,
            description="Missing frontmatter",
            current_value="No frontmatter",
            expected_value="id, title, status, date",
            suggested_fix="Add YAML frontmatter",
            validation="Check manually",
            extra={"source": "audit"},
        )
        assert f.status == FindingStatus.DEFERRED
        assert f.line == 42
        assert f.extra["source"] == "audit"

    def test_to_dict_minimal(self):
        f = Finding(
            finding_id="F-001", scanner="test", file="x.md",
            severity=Severity.LOW, category=Category.C,
        )
        d = f.to_dict()
        assert d["finding_id"] == "F-001"
        assert d["severity"] == "Low"
        assert d["category"] == "C"
        assert "line" not in d
        assert "description" not in d

    def test_to_dict_full(self):
        f = Finding(
            finding_id="F-002", scanner="test", file="x.md",
            severity=Severity.CRITICAL, category=Category.A,
            line=10, description="desc", current_value="cur",
            expected_value="exp", suggested_fix="fix",
            extra={"custom": 1},
        )
        d = f.to_dict()
        assert d["line"] == 10
        assert d["description"] == "desc"
        assert d["custom"] == 1

    def test_to_dict_includes_extra(self):
        f = Finding(
            finding_id="F-003", scanner="test", file="x.md",
            severity=Severity.HIGH, category=Category.B,
            extra={"scope": "all"},
        )
        d = f.to_dict()
        assert d["scope"] == "all"


class TestFindingSet:
    def test_empty(self):
        fs = FindingSet(scanner="test")
        assert fs.count == 0
        assert fs.by_category == {}
        assert fs.by_severity == {}

    def test_single_finding(self):
        f = Finding("F1", "test", "a.md", Severity.HIGH, Category.A)
        fs = FindingSet(scanner="test", findings=[f])
        assert fs.count == 1
        assert Category.A in fs.by_category
        assert len(fs.by_category[Category.A]) == 1
        assert Severity.HIGH in fs.by_severity

    def test_by_category_groups_correctly(self):
        f1 = Finding("F1", "test", "a.md", Severity.LOW, Category.A)
        f2 = Finding("F2", "test", "b.md", Severity.HIGH, Category.B)
        f3 = Finding("F3", "test", "c.md", Severity.MEDIUM, Category.A)
        fs = FindingSet(scanner="test", findings=[f1, f2, f3])
        assert len(fs.by_category[Category.A]) == 2
        assert len(fs.by_category[Category.B]) == 1

    def test_by_severity_groups_correctly(self):
        findings = [
            Finding("F1", "test", "a.md", Severity.CRITICAL, Category.A),
            Finding("F2", "test", "b.md", Severity.CRITICAL, Category.B),
            Finding("F3", "test", "c.md", Severity.LOW, Category.C),
        ]
        fs = FindingSet(scanner="test", findings=findings)
        assert len(fs.by_severity[Severity.CRITICAL]) == 2
        assert len(fs.by_severity[Severity.LOW]) == 1


class TestRule:
    def test_minimal_rule(self):
        r = Rule(rule_id="R-001", description="test rule", severity=Severity.MEDIUM, category=Category.B)
        assert r.rule_id == "R-001"
        assert not r.auto_fixable
        assert r.checker_type == ""

    def test_full_rule(self):
        r = Rule(
            rule_id="R-002", description="full rule", severity=Severity.HIGH,
            category=Category.A, auto_fixable=True, checker_type="content_match",
            params={"pattern": "hello"},
        )
        assert r.auto_fixable
        assert r.checker_type == "content_match"
        assert r.params["pattern"] == "hello"


class TestScanScope:
    def test_default_scope(self):
        s = ScanScope()
        assert s.include_patterns == ["**/*"]
        assert s.exclude_patterns == []
        assert s.repo_root == "."

    def test_match_included(self):
        s = ScanScope(include_patterns=["*.md"])
        assert s.match("readme.md")
        assert not s.match("main.py")

    def test_match_excluded(self):
        s = ScanScope(include_patterns=["*"], exclude_patterns=["*.py"])
        assert s.match("readme.md")
        assert not s.match("main.py")

    def test_match_exclude_overrides_include(self):
        s = ScanScope(include_patterns=["*.md"], exclude_patterns=["README.md"])
        assert s.match("CHANGELOG.md")
        assert not s.match("README.md")
