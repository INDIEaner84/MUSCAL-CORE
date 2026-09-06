"""
Technical Verifier - Deterministische Code-Verifikation.

Führt Tests, statische Analyse und Import-Checks durch.
Kein LLM-Call. Reine Deterministische Verifikation.
"""

import subprocess
import sys
from pathlib import Path
from typing import Any

from features.multi_llm_review.review_schemas import (
    ReviewTask,
    TechnicalVerification,
)


class TechnicalVerifier:
    """Führt deterministische Verifikation durch."""

    def __init__(self, repo_root: Path | None = None):
        self.repo_root = repo_root or Path.cwd()

    def verify(self, task: ReviewTask) -> TechnicalVerification:
        """Führt Tests, statische Analyse, Import-Checks durch."""

        # 1. Tests ausführen
        test_results = self._run_tests()

        # 2. Statische Analyse (pylint/mypy wenn verfügbar)
        static_results = self._run_static_analysis(task.target_files)

        # 3. Import-Validierung
        import_results = self._validate_imports(task.target_files)

        # 4. TechnicalVerification zusammenbauen
        return TechnicalVerification(
            review_task_id=task.task_id,
            tests_passed=test_results["failed"] == 0,
            tests_total=test_results["total"],
            tests_failed=test_results["failed"],
            tests_skipped=test_results["skipped"],
            coverage_pct=test_results["coverage"],
            static_analysis=static_results,
            import_checks=import_results,
            findings=self._extract_findings(test_results, static_results),
        )

    def _run_tests(self) -> dict[str, Any]:
        """Führt pytest aus und parst Results."""
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "--tb=no",
                    "-q",
                    "--collect-only",
                ],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=120,
            )
            # Parse collection output for total count
            lines = result.stdout.strip().split("\n")
            total = 0
            for line in lines:
                if "collected" in line and "items" in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part.isdigit() and i > 0 and parts[i - 1] == "collected":
                            total = int(part)
                            break

            # Run actual tests
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "--tb=no",
                    "-q",
                ],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=300,
            )

            # Parse results
            failed = 0
            skipped = 0
            passed = 0
            for line in result.stdout.split("\n"):
                if "failed" in line and "passed" in line:
                    parts = line.split()
                    for part in parts:
                        if part.endswith("failed"):
                            failed = int(part.replace("failed", ""))
                        elif part.endswith("passed"):
                            passed = int(part.replace("passed", ""))
                        elif part.endswith("skipped"):
                            skipped = int(part.replace("skipped", ""))

            return {
                "total": total or (passed + failed + skipped),
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "coverage": 0.0,  # Would need pytest-cov
                "raw_output": result.stdout,
            }
        except subprocess.TimeoutExpired:
            return {
                "total": 0,
                "passed": 0,
                "failed": 1,
                "skipped": 0,
                "coverage": 0.0,
                "error": "Test timeout",
            }
        except Exception as e:
            return {
                "total": 0,
                "passed": 0,
                "failed": 1,
                "skipped": 0,
                "coverage": 0.0,
                "error": str(e),
            }

    def _run_static_analysis(self, target_files: list[str]) -> dict[str, Any]:
        """Führt statische Analyse durch (pylint/mypy)."""
        results = {"pylint": {}, "mypy": {}}

        # pylint
        try:
            py_files = [f for f in target_files if f.endswith(".py")]
            if py_files:
                result = subprocess.run(
                    [sys.executable, "-m", "pylint", "--output-format=json"] + py_files,
                    cwd=self.repo_root,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                results["pylint"] = {"exit_code": result.returncode, "output": result.stdout[:5000]}
        except FileNotFoundError:
            results["pylint"] = {"error": "pylint not installed"}
        except Exception as e:
            results["pylint"] = {"error": str(e)}

        # mypy
        try:
            if py_files:
                result = subprocess.run(
                    [sys.executable, "-m", "mypy", "--json"] + py_files,
                    cwd=self.repo_root,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                results["mypy"] = {"exit_code": result.returncode, "output": result.stdout[:5000]}
        except FileNotFoundError:
            results["mypy"] = {"error": "mypy not installed"}
        except Exception as e:
            results["mypy"] = {"error": str(e)}

        return results

    def _validate_imports(self, target_files: list[str]) -> dict[str, Any]:
        """Validiert Python Imports."""
        results = {"valid": [], "invalid": []}

        for file_path in target_files:
            if not file_path.endswith(".py"):
                continue
            full_path = self.repo_root / file_path
            if not full_path.exists():
                results["invalid"].append({"file": file_path, "error": "File not found"})
                continue

            try:
                with open(full_path) as f:
                    content = f.read()
                compile(content, file_path, "exec")
                results["valid"].append(file_path)
            except SyntaxError as e:
                results["invalid"].append({"file": file_path, "error": str(e)})
            except Exception as e:
                results["invalid"].append({"file": file_path, "error": str(e)})

        return results

    def _extract_findings(
        self, test_results: dict[str, Any], static_results: dict[str, Any]
    ) -> list[str]:
        """Extrahiert Findings aus Test- und Analyse-Ergebnissen."""
        findings = []

        if test_results.get("failed", 0) > 0:
            findings.append(f"{test_results['failed']} tests failed")

        if test_results.get("error"):
            findings.append(f"Test execution error: {test_results['error']}")

        for tool, result in static_results.items():
            if isinstance(result, dict) and result.get("exit_code", 0) != 0:
                findings.append(f"{tool} found issues (exit code: {result['exit_code']})")

        return findings
