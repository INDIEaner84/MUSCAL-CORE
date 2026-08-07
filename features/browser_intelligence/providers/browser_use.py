"""Browser Intelligence - Browser-Use research provider.

Three execution modes:

1. Extract mode (always): Browser-Use BrowserSession navigates to a search
   engine (Bing -> DuckDuckGo) and reads the page text. No LLM required.
2. Synthesis mode (default): one LLM call (local Ollama preferred) turns the
   extracted text into structured FACTS/ANALYSIS/OPTIONS/RECOMMENDATION.
3. Agent mode (opt-in, BROWSER_INTEL_AGENT=1): full browser-use Agent loop,
   the chat model drives navigation. Requires a fast LLM.

Source engine fallback list: Bing -> DuckDuckGo lite -> DuckDuckGo html.
Facts verified against browser-use 0.13.7 public API.
"""

from __future__ import annotations

import os
import time
import urllib.parse

from ..config import get_config
from ..llm import resolve_chat_llm
from ..models import ResearchFindings, Source
from .base import ResearchProvider

_ENGINES = [
    "https://www.google.com/search?q={query}&gl=us&hl=en&num=10",
    "https://www.bing.com/search?q={query}&setlang=en",
    "https://lite.duckduckgo.com/lite/?q={query}",
    "https://html.duckduckgo.com/html/?q={query}",
]

_SYNTH_SYSTEM = (
    "You are a research assistant. You receive raw text extracted from a web "
    "search for a research question. You must produce a structured answer.\n"
    "Reply with the following sections as plain text:\n"
    "FACTS: bullet points with verified pieces of information\n"
    "ANALYSIS: two to four sentences of engineering interpretation\n"
    "OPTIONS: possible next steps or solutions, one per line\n"
    "RECOMMENDATION: the single most useful next action\n"
    "CONFIDENCE: Low, Medium or High based on how directly the source text "
    "answers the question."
)


class BrowserUseProvider(ResearchProvider):

    name = "browser_use"

    async def research(self, question, topic="", constraints=None):
        started = time.time()
        warnings = []
        cfg = get_config()
        task = question
        if topic:
            task = f"{topic}: {question}"
        if constraints:
            task = task + "\nConstraints: " + "; ".join(constraints)

        os.environ.setdefault("TIMEOUT_BrowserStartEvent", str(cfg.start_timeout))
        os.environ.setdefault("TIMEOUT_BrowserLaunchEvent", str(cfg.launch_timeout))
        os.environ.setdefault("TIMEOUT_NavigateToUrlEvent", str(cfg.nav_timeout))

        llm = resolve_chat_llm()

        if llm is not None and cfg.agent_mode:
            try:
                findings = await self._research_with_agent(task, llm, cfg)
                findings.elapsed_ms = int((time.time() - started) * 1000)
                return findings
            except Exception as exc:
                warnings.append(f"Agent mode failed ({exc})")

        findings = await self._research_extract(task, cfg, warnings)

        if llm is not None and cfg.synthesize:
            try:
                findings = await self._synthesize(task, findings, llm, cfg)
            except Exception as exc:
                warnings.append(
                    f"Synthesis failed ({type(exc).__name__}: {exc}); kept raw extraction"
                )

        findings.elapsed_ms = int((time.time() - started) * 1000)
        return findings

    async def _research_with_agent(self, task, llm, cfg):
        from browser_use import Agent

        agent = Agent(
            task=task,
            llm=llm,
            use_vision=False,
            step_timeout=300,
            llm_timeout=240,
        )
        history = await agent.run(max_steps=cfg.max_steps)
        final = ""
        try:
            final = history.final_result() or ""
        except Exception:
            pass
        urls = []
        try:
            urls = history.urls() or []
        except Exception:
            pass

        facts = [f.strip() for f in (final.splitlines() if final else []) if f.strip()]
        if not facts and final:
            facts = [final]

        sources = []
        seen = set()
        for u in urls:
            if u and u not in seen:
                seen.add(u)
                sources.append(Source(url=u, title=""))

        confidence = "High" if facts and sources else "Medium"
        return ResearchFindings(
            question=task,
            facts=facts,
            analysis=(
                "Synthesised from a live browser session. "
                "Cross-check claims against the listed sources."
            ),
            options=[f"Read source: {s.url}" for s in sources] or ["Re-run with more steps"],
            recommendation="Validate the facts above against the sources, then apply.",
            confidence=confidence,
            provider=self.name,
            sources=sources,
            warnings=[],
        )

    async def _research_extract(self, task, cfg, warnings):
        from browser_use.browser.session import BrowserSession

        clean_query = " ".join(task.replace("\n", " ").split())
        clean_query = clean_query[:160]
        if not clean_query:
            clean_query = "web search"
        query = urllib.parse.quote(clean_query)
        page_text = ""
        engine_used = ""
        attempts = max(1, int(getattr(cfg, "browser_retries", 1)))
        for attempt in range(attempts):
            session = None
            try:
                session = BrowserSession(
                    headless=cfg.headless,
                    executable_path=cfg.chromium or None,
                    enable_default_extensions=False,
                    user_agent=(
                        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
                    ),
                )
                await session.start()
                for engine in _ENGINES:
                    url = engine.format(query=query)
                    try:
                        await session.navigate_to(url)
                        state = await session.get_state_as_text()
                    except Exception:
                        continue
                    if state and len(state.strip()) > 30 and not self._looks_like_captcha(state):
                        page_text = state
                        engine_used = url
                        break
                break
            except Exception as exc:
                if attempt + 1 < attempts:
                    warnings.append(f"Browser attempt {attempt + 1}/{attempts} failed ({exc})")
                else:
                    warnings.append(f"Browser failed after {attempts} attempts ({exc})")
            finally:
                if session is not None:
                    try:
                        await session.stop()
                    except Exception:
                        pass

        facts = self._parse_facts_from_text(page_text, cfg.max_results)
        if not facts:
            facts = ["No extractable content. Search engine likely blocked the request."]
        if not engine_used:
            warnings.append("All search engines failed; no page was read.")

        sources = []
        if engine_used:
            sources.append(Source(url=engine_used, title="search results"))
        return ResearchFindings(
            question=task,
            facts=facts,
            analysis=(
                "Extract mode: raw search engine text, no LLM synthesis yet."
            ),
            options=["LLM synthesis (default)", "Re-run as browser-use Agent"],
            recommendation="Let the LLM synthesise these raw extracts (default).",
            confidence="Low",
            provider=self.name,
            sources=sources,
            warnings=warnings,
        )

    async def _synthesize(self, task, findings, llm, cfg):
        from browser_use.llm import SystemMessage, UserMessage

        from ..llm import resolve_synthesis_llm

        synth_llm = resolve_synthesis_llm()
        effective = synth_llm or llm

        raw = "\n".join("- " + f for f in findings.facts)
        response = await effective.ainvoke(
            [
                SystemMessage(content=_SYNTH_SYSTEM),
                UserMessage(
                    content=f"Research question:\n{task}\n\n"
                    f"Source page: {findings.sources[0].url if findings.sources else 'n/a'}\n"
                    f"Extracted text:\n{raw[:6000]}"
                ),
            ]
        )
        answer = (response.completion or "").strip()
        if not answer:
            return findings

        sections = self._split_sections(answer)
        conf_lines = self._section_lines(sections, "CONFIDENCE")
        confidence = conf_lines[0] if conf_lines else ""
        if confidence not in ("Low", "Medium", "High"):
            confidence = "Medium"

        facts = self._section_lines(sections, "FACTS") or findings.facts
        return ResearchFindings(
            question=task,
            facts=[f[:400] for f in facts[: cfg.max_results * 2]],
            analysis="\n".join(self._section_lines(sections, "ANALYSIS")) or findings.analysis,
            options=self._section_lines(sections, "OPTIONS")
            or findings.options or ["No next step captured"],
            recommendation="\n".join(self._section_lines(sections, "RECOMMENDATION")).strip()
            or findings.recommendation,
            confidence=confidence,
            provider=self.name,
            sources=findings.sources,
            warnings=findings.warnings,
        )

    def _split_sections(self, text):
        sections = {}
        current = "UNKNOWN"
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            upper = stripped.upper()
            for name in ("FACTS:", "ANALYSIS:", "OPTIONS:", "RECOMMENDATION:", "CONFIDENCE:"):
                if upper.startswith(name) or upper == name.rstrip(":"):
                    current = name.rstrip(":")
                    sections.setdefault(current, [])
                    rest = stripped[len(name):].strip()
                    if rest:
                        sections[current].append(rest)
                    break
            else:
                sections.setdefault(current, []).append(stripped)
        return sections

    def _section_lines(self, sections, name):
        return [ln.strip("-• \t") for ln in sections.get(name, []) if ln.strip()]

    def _looks_like_captcha(self, text: str) -> bool:
        markers = (
            "unusual traffic",
            "not a robot",
            "ich bin kein roboter",
            "captcha",
            "verify you are a human",
            "sorry, no robots allowed",
        )
        lowered = text.lower()
        return any(m in lowered for m in markers)

    def _parse_facts_from_text(self, text, limit):
        noise = (
            "|scroll element|",
            "|SHADOW(",
            "role=",
            "aria-label=",
            "id=b_",
            "id=sb_",
            "id=APjFqb",
            "maxlength=",
            "a11y_feedback",
            "Barrierefreiheit",
            "Go to Google Home",
            "Duplicate",
        )
        facts = []
        for ln in text.splitlines():
            ln = ln.strip()
            if not ln or len(ln) <= 20:
                continue
            if ln.startswith("|"):
                continue
            if ln.startswith("[") and "<" in ln:
                continue
            if any(n in ln for n in noise):
                continue
            facts.append(ln[:400])
            if len(facts) >= limit:
                break
        return facts