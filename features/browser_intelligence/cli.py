"""Browser Intelligence - CLI entry point.

Usage:
    .venv/bin/python -m features.browser_intelligence.cli "research question"
"""

from __future__ import annotations

import sys


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    question = " ".join(argv) or "Summarize the installation requirements of browser-use."
    from .research_service import ResearchService

    findings = ResearchService().research(question)
    print(findings.to_markdown())
    return 0


if __name__ == "__main__":
    sys.exit(main())
