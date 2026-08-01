from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .project_scanner import ProjectContext
from .result_normalizer import NormalizedResult


@dataclass
class BridgeReport:
    project: ProjectContext
    task: dict
    execution: NormalizedResult
    changes: list[dict] = field(default_factory=list)
    tests: list[dict] = field(default_factory=list)
    risks: list[dict] = field(default_factory=list)
    next_action: str = ""
    generated_at: str = ""

    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.now(timezone.utc).isoformat()

    def to_markdown(self) -> str:
        lines = [
            "# Bridge Execution Report",
            "",
            f"**Generated:** {self.generated_at}",
            "",
            "## Project",
            f"- Root: `{self.project.root}`",
            f"- Branch: `{self.project.branch}`",
            f"- Commit: `{self.project.commit}`",
            f"- Dirty: {self.project.git.dirty}",
            "",
            "## Task",
            f"- ID: {self.task.get('id', 'unknown')}",
            f"- Description: {self.task.get('description', 'unknown')}",
            "",
            "## Execution",
            f"- Status: {self.execution.status}",
            f"- Duration: {self.execution.execution.duration:.2f}s" if self.execution.execution else "- Duration: unknown",
            f"- Session: {self.execution.execution.session_reference}" if self.execution.execution and self.execution.execution.session_reference else "- Session: none",
            "",
            "### Verified Facts",
        ]
        if self.execution.facts:
            for f in self.execution.facts:
                lines.append(f"- {f.statement} (source: {f.source})")
        else:
            lines.append("- None")

        lines.extend(["", "### Observations"])
        if self.execution.observations:
            for o in self.execution.observations:
                lines.append(f"- {o.statement} (source: {o.source})")
        else:
            lines.append("- None")

        lines.extend(["", "### Interpretations"])
        if self.execution.interpretations:
            for i in self.execution.interpretations:
                lines.append(f"- {i.statement} (confidence: {i.confidence})")
        else:
            lines.append("- None")

        lines.extend(["", "### Unknowns"])
        if self.execution.unknowns:
            for u in self.execution.unknowns:
                lines.append(f"- {u}")
        else:
            lines.append("- None")

        lines.extend(["", "### Changes"])
        if self.changes:
            for c in self.changes:
                lines.append(f"- {c.get('file', 'unknown')}: {c.get('description', '')}")
        else:
            lines.append("- None")

        lines.extend(["", "### Tests"])
        if self.tests:
            lines.append(f"| Test | Status |")
            lines.append(f"|------|--------|")
            for t in self.tests:
                lines.append(f"| {t.get('name', '')} | {t.get('status', '')} |")
        else:
            lines.append("- None")

        lines.extend(["", "### Risks"])
        if self.risks:
            for r in self.risks:
                lines.append(f"- [{r.get('priority', 'P3')}] {r.get('description', '')}")
        else:
            lines.append("- None")

        lines.extend(["", "## Next Recommended Action", "", self.next_action or "None specified"])
        return "\n".join(lines) + "\n"

    def to_yaml(self) -> str:
        d = self.to_dict()
        return _dict_to_yaml(d)

    def to_dict(self) -> dict:
        return {
            "report": {
                "generated_at": self.generated_at,
                "project": {
                    "root": str(self.project.root),
                    "branch": self.project.branch,
                    "commit": self.project.commit,
                    "dirty": self.project.git.dirty,
                },
                "task": self.task,
                "execution": self.execution.to_dict().get("result", {}),
                "changes": self.changes,
                "tests": self.tests,
                "risks": self.risks,
                "next_action": self.next_action,
            }
        }


def _dict_to_yaml(d: dict, indent: int = 0) -> str:
    lines: list[str] = []
    prefix = "  " * indent
    for key, value in d.items():
        k = str(key)
        if isinstance(value, dict):
            lines.append(f"{prefix}{k}:")
            lines.append(_dict_to_yaml(value, indent + 1))
        elif isinstance(value, list):
            lines.append(f"{prefix}{k}:")
            for item in value:
                if isinstance(item, dict):
                    lines.append(f"{prefix}  -")
                    lines.append(_dict_to_yaml(item, indent + 2))
                else:
                    lines.append(f"{prefix}  - {_yaml_scalar(item)}")
        elif isinstance(value, bool):
            lines.append(f"{prefix}{k}: {'true' if value else 'false'}")
        elif value is None:
            lines.append(f"{prefix}{k}: null")
        else:
            lines.append(f"{prefix}{k}: {_yaml_scalar(value)}")
    return "\n".join(lines)


def _yaml_scalar(value: Any) -> str:
    s = str(value)
    if ":" in s or "#" in s or s.startswith(" ") or s.endswith(" "):
        return f'"{s}"'
    return s


class HandoffReport:

    def __init__(self, output_dir: Optional[Path] = None):
        self._output_dir = output_dir

    def generate(self, report: BridgeReport,
                 markdown_path: Optional[Path] = None,
                 yaml_path: Optional[Path] = None) -> tuple[Path, Path]:
        md_path = markdown_path or self._resolve_path("md")
        yml_path = yaml_path or self._resolve_path("yaml")

        md_path.parent.mkdir(parents=True, exist_ok=True)
        yml_path.parent.mkdir(parents=True, exist_ok=True)

        md_path.write_text(report.to_markdown(), encoding="utf-8")
        yml_path.write_text(report.to_yaml(), encoding="utf-8")

        return md_path, yml_path

    def _resolve_path(self, ext: str) -> Path:
        base = self._output_dir or Path("docs/bridge/handovers")
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        return base / f"handover_{ts}.{ext}"
