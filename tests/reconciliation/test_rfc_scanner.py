import os
import tempfile

from reconciliation.core.context import ScanContext
from reconciliation.core.finding import Category, Severity
from reconciliation.core.scope import ScanScope
from reconciliation.scan.rfc_scanner import RfcValidatorScanner
from reconciliation.snapshot.file_node import FileNode
from reconciliation.snapshot.repository_snapshot import RepositorySnapshot


class TestRfcValidatorScanner:
    def test_name(self):
        scanner = RfcValidatorScanner()
        assert scanner.name == "rfc_validator_scanner"

    def test_rules(self):
        scanner = RfcValidatorScanner()
        rules = scanner.rules
        assert len(rules) == 3
        rule_ids = [r.rule_id for r in rules]
        assert "RFC-001" in rule_ids
        assert "RFC-002" in rule_ids
        assert "RFC-003" in rule_ids

    def test_scan_no_snapshot(self):
        scanner = RfcValidatorScanner()
        ctx = ScanContext()
        result = scanner.scan(ctx)
        assert result.count == 0
        assert result.scanner == "rfc_validator_scanner"

    def test_is_rfc_by_filename(self):
        node = FileNode(
            rel_path="RFC-001-implementation.md",
            abs_path="/tmp/RFC-001-implementation.md",
            size=0, extension=".md", directory="",
            filename="RFC-001-implementation.md", modified=0.0,
        )
        scanner = RfcValidatorScanner()
        assert scanner._is_rfc(node)

    def test_is_rfc_by_filename_case_insensitive(self):
        node = FileNode(
            rel_path="rfc_002_test.md",
            abs_path="/tmp/rfc_002_test.md",
            size=0, extension=".md", directory="",
            filename="rfc_002_test.md", modified=0.0,
        )
        scanner = RfcValidatorScanner()
        assert scanner._is_rfc(node)

    def test_is_not_rfc_non_matching_filename(self):
        node = FileNode(
            rel_path="README.md",
            abs_path="/tmp/README.md",
            size=0, extension=".md", directory="",
            filename="README.md", modified=0.0,
        )
        scanner = RfcValidatorScanner()
        assert not scanner._is_rfc(node)

    def test_check_frontmatter_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "RFC-001-test.md")
            with open(filepath, "w") as f:
                f.write("# RFC-001\n\nSome content")

            node = FileNode.from_abs_path(filepath, tmpdir)
            scanner = RfcValidatorScanner()
            findings = scanner._check_frontmatter([node])
            assert len(findings) == 1
            assert findings[0].finding_id.startswith("RFC-001")
            assert findings[0].severity == Severity.MEDIUM
            assert findings[0].category == Category.B
            assert "missing frontmatter" in findings[0].description.lower()

    def test_check_frontmatter_valid(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "RFC-001-test.md")
            frontmatter = (
                "---\n"
                "id: RFC-001\n"
                "title: Test RFC\n"
                "status: PROPOSED\n"
                "date: 2026-07-15\n"
                "---\n"
                "\n"
                "# RFC-001\n"
            )
            with open(filepath, "w") as f:
                f.write(frontmatter)

            node = FileNode.from_abs_path(filepath, tmpdir)
            scanner = RfcValidatorScanner()
            findings = scanner._check_frontmatter([node])
            assert len(findings) == 0

    def test_check_frontmatter_missing_field(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "RFC-002-test.md")
            frontmatter = (
                "---\n"
                "id: RFC-002\n"
                "title: Missing fields\n"
                "---\n"
                "\n"
                "# RFC-002\n"
            )
            with open(filepath, "w") as f:
                f.write(frontmatter)

            node = FileNode.from_abs_path(filepath, tmpdir)
            scanner = RfcValidatorScanner()
            findings = scanner._check_frontmatter([node])
            assert len(findings) == 1
            assert "missing" in findings[0].description.lower()

    def test_check_required_sections_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "RFC-003-test.md")
            content = "---\nid: RFC-003\ntitle: Test\nstatus: DRAFT\ndate: 2026-07-15\n---\n\n# RFC-003\n\nSome content"
            with open(filepath, "w") as f:
                f.write(content)

            node = FileNode.from_abs_path(filepath, tmpdir)
            scanner = RfcValidatorScanner()
            findings = scanner._check_required_sections([node])
            assert len(findings) == 1
            assert findings[0].finding_id.startswith("RFC-002")

    def test_check_required_sections_present(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "RFC-004-test.md")
            content = (
                "---\nid: RFC-004\ntitle: Test\nstatus: DRAFT\ndate: 2026-07-15\n---\n\n"
                "# RFC-004\n\n"
                "## Motivation\n\nmotive\n\n"
                "## Specification\n\nspec\n\n"
                "## Decision\n\ndecision\n\n"
                "## Consequences\n\nconsequences\n"
            )
            with open(filepath, "w") as f:
                f.write(content)

            node = FileNode.from_abs_path(filepath, tmpdir)
            scanner = RfcValidatorScanner()
            findings = scanner._check_required_sections([node])
            assert len(findings) == 0

    def test_check_numbering_duplicate(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path1 = os.path.join(tmpdir, "RFC-001-first.md")
            path2 = os.path.join(tmpdir, "RFC-001-second.md")
            for p in [path1, path2]:
                with open(p, "w") as f:
                    f.write(f"# RFC-001\n")

            node1 = FileNode.from_abs_path(path1, tmpdir)
            node2 = FileNode.from_abs_path(path2, tmpdir)
            scanner = RfcValidatorScanner()
            findings = scanner._check_numbering([node1, node2])
            dupes = [f for f in findings if "duplicate" in f.description.lower()]
            assert len(dupes) >= 1

    def test_scan_on_real_repo(self):
        scanner = RfcValidatorScanner()
        snapshot = RepositorySnapshot()
        snapshot.build()
        scope = snapshot.to_scan_scope()
        ctx = ScanContext(snapshot=snapshot, scope=scope)
        result = scanner.scan(ctx)
        assert result.scanner == "rfc_validator_scanner"
        assert isinstance(result.count, int)
