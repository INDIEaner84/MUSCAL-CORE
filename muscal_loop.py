#!/usr/bin/env python3
import datetime
import json
import os
import re
import subprocess

from kernel_diff_engine import KernelDiffEngine, ReplayEngine, StateStore, link_trace_to_state
from mcxf_fusion import get_memory_context, store_mcxf
from mcxf_graph_builder import store_mcxf_graph
from trace_engine import log_step, print_trace, reset_trace

# ────────────────────────────────────────────
# CONFIG
# ────────────────────────────────────────────

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:7b-instruct"
MAX_ITERATIONS = 3

ALLOWED_TOOLS = [
    "browser.open", "browser.click", "browser.type",
    "console.print", "opencode.run", "file.write",
]
ALLOWED_TOOLS_SET = set(ALLOWED_TOOLS)

ALLOWED_OPENCODE_COMMANDS = ["ls", "cat", "echo", "python3 -c", "pwd", "wc", "head", "tail"]
ALLOWED_FILE_PATHS = ["./output/", "./storage/", "/tmp/"]

# ────────────────────────────────────────────
# 1. TOOL SCHEMAS
# ────────────────────────────────────────────

TOOL_SCHEMAS = {
    "console.print": {
        "args": {"message": str},
    },
    "browser.open": {
        "args": {"url": str},
    },
    "browser.click": {
        "args": {"selector": str},
    },
    "browser.type": {
        "args": {"selector": str, "text": str},
    },
    "opencode.run": {
        "args": {"command": str},
    },
    "file.write": {
        "args": {"path": str, "content": str},
    },
}

# ────────────────────────────────────────────
# 2. BROWSER AGENT (Playwright lifecycle)
# ────────────────────────────────────────────

class BrowserAgent:
    def __init__(self, headless=False):
        self._playwright = None
        self._browser = None
        self._page = None
        self.headless = headless
        self._available = False

    def start(self):
        try:
            from playwright.sync_api import sync_playwright
            self._pw = sync_playwright()
            self._playwright = self._pw.__enter__()
            self._browser = self._playwright.chromium.launch(headless=self.headless)
            self._page = self._browser.new_page()
            self._available = True
        except ImportError:
            self._available = False

    @property
    def available(self):
        return self._available

    def open(self, url):
        if not self._available:
            return {"status": "stub", "title": "stub", "url": url}
        self._page.goto(url, timeout=15000)
        return {"status": "opened", "title": self._page.title(), "url": url}

    def click(self, selector):
        if not self._available:
            return {"status": "stub", "selector": selector}
        self._page.click(selector)
        return {"status": "clicked", "selector": selector}

    def type_text(self, selector, text):
        if not self._available:
            return {"status": "stub", "selector": selector, "text": text}
        self._page.fill(selector, text)
        return {"status": "typed", "selector": selector, "text": text}

    def close(self):
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.__exit__(None, None, None)

    def screenshot(self, path="screenshot.png"):
        if not self._available:
            return {"status": "stub", "path": path}
        self._page.screenshot(path=path)
        return {"status": "saved", "path": path}


_browser = BrowserAgent(headless=False)

# ────────────────────────────────────────────
# 3. LLM CONNECTOR
# ────────────────────────────────────────────

SYSTEM_PROMPT = """You are operating inside the MUSCAL Kernel.

Strict rules:

- Compute Layer: no tools, no side effects
- Execution Layer: only tool-based actions
- Observability Layer: logging only, no influence on execution

Hard constraints:
- TRACE must never influence COMPUTE or EXECUTION
- EXECUTION must never call COMPUTE or TRACE
- COMPUTE must not access tools, filesystem, browser or logs

Available tools (Execution Layer only):
- console.print: args {"message": str}
- browser.open: args {"url": str}
- browser.click: args {"selector": str}
- browser.type: args {"selector": str, "text": str}
- opencode.run: args {"command": str}
- file.write: args {"path": str, "content": str}

Output:
- Return ONLY valid MCXF JSON
- No explanations
- No markdown
- Format: {"tasks": [{"tool": "...", "args": {...}}]}
- NEVER include shell metacharacters"""


# ── Stub LLM (zero deps, deterministic) ──

STUB_KEYWORDS = {
    "opencode.run": [
        r"\bls\b", r"\bcat\b", r"\becho\b", r"\blist\b", r"\bdir\b",
        r"\bfiles\b", r"\bdirectory\b",
    ],
    "browser.open": [
        r"\bopen\b.*\bhttps?://", r"\bgo to\b", r"\bnavigate\b",
        r"\bgithub\b", r"\bgoogle\b", r"\burl\b",
    ],
    "browser.click": [
        r"\bclick\b", r"\bpress\b", r"\btap\b",
    ],
    "browser.type": [
        r"\btype\b.*\binto\b", r"\bfill\b", r"\benter\b.*\b(?:in|into)\b",
    ],
    "console.print": [
        r"\bprint\b", r"\bsay\b", r"\bhello\b", r"\bshow\b",
        r"\boutput\b", r"\bdisplay\b",
    ],
    "file.write": [
        r"\bwrite\b", r"\bcreate file\b", r"\bsave\b",
    ],
}


def _stub_llm(user_input, context=""):
    tasks = []
    text = user_input.lower()

    for tool, patterns in STUB_KEYWORDS.items():
        for pat in patterns:
            if re.search(pat, text):
                if tool == "console.print":
                    match = re.search(r"print\s+(.+)", text)
                    msg = match.group(1).strip().strip("\"'") if match else user_input
                    tasks.append({"tool": "console.print", "args": {"message": msg}})
                    break
                elif tool == "browser.open":
                    match = re.search(r"(https?://\S+)", text)
                    url = match.group(1) if match else "https://github.com"
                    tasks.append({"tool": "browser.open", "args": {"url": url}})
                    break
                elif tool == "browser.click":
                    match = re.search(r"click\s+(?:on\s+)?[\"']?([^\"']+)[\"']?", text)
                    sel = match.group(1).strip() if match else "body"
                    tasks.append({"tool": "browser.click", "args": {"selector": sel}})
                    break
                elif tool == "browser.type":
                    m = re.search(
                        r"(?:type|enter|fill)\s+[\"']([^\"']+)[\"']\s+(?:into|in)\s+[\"']([^\"']+)[\"']",
                        text,
                    )
                    if m:
                        tasks.append({"tool": "browser.type", "args": {"selector": m.group(2).strip(), "text": m.group(1).strip()}})
                    else:
                        tasks.append({"tool": "browser.type", "args": {"selector": "input", "text": "hello"}})
                    break
                elif tool == "opencode.run":
                    match = re.search(r"(?:run|execute|list|cat|echo)\s+(.+)", text)
                    cmd = match.group(1).strip().strip("\"'") if match else text
                    tasks.append({"tool": "opencode.run", "args": {"command": cmd}})
                    break
                elif tool == "file.write":
                    match = re.search(r"write\s+(.+?)(?:\s+with\s+content\s+(.+))?$", text)
                    if match:
                        path = match.group(1).strip()
                        content = match.group(2).strip() if match.group(2) else user_input
                    else:
                        path = "output.txt"
                        content = user_input
                    tasks.append({"tool": "file.write", "args": {"path": path, "content": content}})
                    break

    if not tasks:
        tasks.append({"tool": "console.print", "args": {"message": user_input}})

    return json.dumps({"tasks": tasks})


# ── Ollama LLM (Qwen 2.5) ──

def _ollama_llm(user_input, context=""):
    prompt = SYSTEM_PROMPT
    if context:
        prompt += f"\nPrevious iteration results:\n{context}"
    prompt += f"\n\nUser: {user_input}"

    import requests
    try:
        r = requests.post(OLLAMA_URL, json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
        }, timeout=60)
        data = r.json()
        return data.get("response", "")
    except Exception:
        return _stub_llm(user_input, context)


def llm_compile(user_input, context="", use_ollama=False):
    if use_ollama:
        return _ollama_llm(user_input, context)
    return _stub_llm(user_input, context)


# ────────────────────────────────────────────
# 4. MCXF PARSER
# ────────────────────────────────────────────

def parse_mcxf(raw_text):
    match = re.search(r'\{.*"tasks".*\}', raw_text, re.DOTALL)
    if not match:
        return {"tasks": [{"tool": "console.print", "args": {"message": raw_text.strip()[:200]}}]}
    try:
        data = json.loads(match.group(0))
        if "tasks" not in data or not isinstance(data["tasks"], list):
            raise ValueError("missing tasks list")
        return data
    except (json.JSONDecodeError, ValueError):
        return {"tasks": [{"tool": "console.print", "args": {"message": raw_text.strip()[:200]}}]}


# ────────────────────────────────────────────
# 5. VALIDATOR (SAFETY GATE)
# ────────────────────────────────────────────

def validate_tasks(tasks):
    errors = []
    if not isinstance(tasks, list):
        return False, ["tasks must be a list"]
    for i, task in enumerate(tasks):
        if not isinstance(task, dict):
            errors.append(f"task[{i}] must be a dict")
            continue
        tool = task.get("tool", "")
        if tool not in ALLOWED_TOOLS_SET:
            errors.append(f"task[{i}]: tool '{tool}' not in ALLOWED_TOOLS — rejected")
            continue
        if tool not in TOOL_SCHEMAS:
            errors.append(f"task[{i}]: unknown tool '{tool}'")
            continue
        args = task.get("args", {})
        schema = TOOL_SCHEMAS[tool]
        for key, expected_type in schema["args"].items():
            if key not in args:
                errors.append(f"task[{i}].args missing '{key}'")
                continue
            if not isinstance(args[key], expected_type):
                errors.append(
                    f"task[{i}].args['{key}'] expected {expected_type.__name__}, "
                    f"got {type(args[key]).__name__}"
                )
        for k, v in args.items():
            if isinstance(v, str):
                if re.search(r'[;&|`$(){}\n\r]', v):
                    errors.append(f"task[{i}].args['{k}'] contains shell metacharacters")
    return len(errors) == 0, errors


def validate_safe_path(path):
    for prefix in ALLOWED_FILE_PATHS:
        if path.startswith(prefix) or os.path.abspath(path).startswith(os.path.abspath(prefix)):
            return True
    return False


# ────────────────────────────────────────────
# 6. TOOL EXECUTOR (MEL)
# ────────────────────────────────────────────

def _exec_console_print(args):
    print(args["message"])
    return {"printed": args["message"]}


def _exec_browser_open(args):
    return _browser.open(args["url"])


def _exec_browser_click(args):
    return _browser.click(args["selector"])


def _exec_browser_type(args):
    return _browser.type_text(args["selector"], args["text"])


def _exec_opencode_run(args):
    command = args["command"]
    stripped = command.strip()
    allowed = any(stripped.startswith(c) or stripped == c for c in ALLOWED_OPENCODE_COMMANDS)
    if allowed:
        try:
            import shlex
            parts = shlex.split(stripped)
            result = subprocess.run(parts, capture_output=True, text=True, timeout=10)
            output = (result.stdout or result.stderr).strip()
            return {"status": "ok", "command": command, "output": output[:2000]}
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "command": command}
        except Exception as e:
            return {"status": "error", "command": command, "error": str(e)}
    return {
        "status": "blocked", "command": command,
        "error": f"command not in allowlist: {ALLOWED_OPENCODE_COMMANDS}",
    }


def _exec_file_write(args):
    path = args["path"]
    if not validate_safe_path(path):
        return {"status": "blocked", "path": path, "error": f"path not allowed: {ALLOWED_FILE_PATHS}"}
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            f.write(args["content"])
        return {"status": "written", "path": os.path.abspath(path)}
    except Exception as e:
        return {"status": "error", "path": path, "error": str(e)}


EXECUTORS = {
    "console.print": _exec_console_print,
    "browser.open": _exec_browser_open,
    "browser.click": _exec_browser_click,
    "browser.type": _exec_browser_type,
    "opencode.run": _exec_opencode_run,
    "file.write": _exec_file_write,
}


def execute_tool(task):
    tool = task["tool"]
    args = task["args"]
    fn = EXECUTORS.get(tool)
    if fn is None:
        return {"tool": tool, "status": "unknown_tool"}
    try:
        result = fn(args)
        result["tool"] = tool
        return result
    except Exception as e:
        return {"tool": tool, "status": "error", "error": str(e)}


# ────────────────────────────────────────────
# 7. FEEDBACK LOOP CONTROLLER
# ────────────────────────────────────────────

def build_feedback(results):
    parts = []
    for r in results:
        if "printed" in r:
            parts.append(f"console.print → '{r['printed']}'")
        elif r.get("status") in ("opened", "stub"):
            parts.append(f"browser.open → {r.get('title', r.get('url', ''))}")
        elif r.get("status") == "clicked":
            parts.append(f"browser.click → {r.get('selector', '')}")
        elif r.get("status") == "typed":
            parts.append(f"browser.type → {r.get('selector', '')}")
        elif r.get("status") == "ok":
            parts.append(f"opencode.run → {r.get('output', 'ok')[:100]}")
        elif r.get("status") == "written":
            parts.append(f"file.write → {r.get('path', '')}")
        else:
            parts.append(f"{r.get('tool', '?')} → {r.get('status', '?')}")
    return "; ".join(parts)


class MuscalLoop:
    def __init__(self, use_ollama=False):
        self.use_ollama = use_ollama
        self.history = []
        self.state_store = StateStore()
        self.diff_engine = KernelDiffEngine()
        self.replay_engine = ReplayEngine()

    def run(self, user_input):
        reset_trace()
        run_id = datetime.datetime.utcnow().isoformat()
        _browser.start()
        context = ""
        iteration = 0
        all_results = []

        log_step("OBSERVABILITY", "LOOP_START", {"run_id": run_id, "input": user_input}, trace_level=0)

        try:
            while iteration < MAX_ITERATIONS:
                iteration += 1

                log_step("COMPUTE", "LLM_COMPILE", {"input": user_input[:100], "iteration": iteration}, trace_level=1)
                mem_ctx = get_memory_context(user_input)
                rag_prompt = user_input
                if mem_ctx:
                    graph_part = json.dumps(mem_ctx.get("graph", []))
                    cosine_part = json.dumps(mem_ctx.get("cosine", []))
                    rag_prompt = f"COSINE CONTEXT:\n{cosine_part}\n\nGRAPH CONTEXT:\n{graph_part}\n\nINPUT:\n{user_input}"
                raw = llm_compile(rag_prompt, context, use_ollama=self.use_ollama)
                log_step("COMPUTE", "LLM_RAW", {"raw": raw[:200], "iteration": iteration}, trace_level=2)

                mcxf = parse_mcxf(raw)
                tasks = mcxf.get("tasks", [])
                tool_names = [t.get("tool", "?") for t in tasks]
                log_step("COMPUTE", "MCXF_OUTPUT", {"tasks": len(tasks), "tools": tool_names, "iteration": iteration}, trace_level=1)

                snapshots = self.state_store.get(run_id)
                if snapshots:
                    before = snapshots[-1]
                    diff = self.diff_engine.diff(before, mcxf)
                    log_step("OBSERVABILITY", "STATE_DIFF", diff, trace_level=0)
                self.state_store.save(run_id, mcxf)

                if not tasks:
                    log_step("OBSERVABILITY", "LOOP_BREAK", {"reason": "empty tasks", "iteration": iteration}, trace_level=1)
                    break

                ok, errors = validate_tasks(tasks)
                log_step("EXECUTION", "TASK_VALIDATE", {"ok": ok, "errors": errors[:5], "iteration": iteration}, trace_level=1)
                if not ok:
                    context = f"validation errors: {'; '.join(errors)}"
                    continue

                results = []
                for t in tasks:
                    log_step("EXECUTION", "TASK_EXEC", {"tool": t["tool"], "args": t["args"], "iteration": iteration}, trace_level=0)
                    r = execute_tool(t)
                    results.append(r)

                all_results.extend(results)

                feedback = build_feedback(results)
                log_step("OBSERVABILITY", "FEEDBACK", {"feedback": feedback, "iteration": iteration}, trace_level=2)

                self.history.append({
                    "iteration": iteration,
                    "mcxf": mcxf,
                    "results": results,
                    "feedback": feedback,
                })

                context = feedback
                log_step("OBSERVABILITY", "ITERATION_END", {"iteration": iteration, "task_count": len(tasks)}, trace_level=1)

                if len(tasks) == 1 and tasks[0]["tool"] == "console.print":
                    break
        finally:
            _browser.close()

        log_step("OBSERVABILITY", "LOOP_END", {"iterations": iteration, "total_tasks": len(all_results)}, trace_level=0)
        if self.history:
            mcxf_doc = {
                "input": user_input,
                "mcxf": self.history[-1]["mcxf"],
                "results": [r for r in all_results if r.get("tool")],
                "timestamp": run_id,
            }
            store_mcxf(mcxf_doc)
            store_mcxf_graph(mcxf_doc)

        return {
            "run_id": run_id,
            "iterations": iteration,
            "tasks_executed": len(all_results),
            "results": all_results,
            "history": self.history,
            "state_snapshots": len(self.state_store.get(run_id)),
        }


# ────────────────────────────────────────────
# 8. VALIDATION GATE (standalone)
# ────────────────────────────────────────────

def validate(mcxf: dict):
    if "tasks" not in mcxf:
        return False
    for task in mcxf["tasks"]:
        if task.get("tool") not in ALLOWED_TOOLS_SET:
            return False
    return True


# ────────────────────────────────────────────
# 9. DEMO
# ────────────────────────────────────────────

def demo():
    print("MUSCAL Autonomous Loop")
    print(f"  Model : {MODEL}")
    print(f"  Tools : {', '.join(ALLOWED_TOOLS)}")
    print(f"  Browser: {'Playwright' if _browser.available else 'stub (no playwright)'}")
    print("=" * 40)

    loop = MuscalLoop(use_ollama=False)
    result = loop.run("open github and print hello")

    for h in result["history"]:
        print(f"\nIteration {h['iteration']}:")
        print(f"  MCXF: {json.dumps(h['mcxf'])}")
        for r in h["results"]:
            print(f"  Result: {json.dumps(r)}")
        print(f"  Feedback: {h['feedback']}")

    print(f"\n{'=' * 40}")
    print(f"Iterations     : {result['iterations']}")
    print(f"Tasks executed : {result['tasks_executed']}")
    assert result["tasks_executed"] >= 1, "no tools executed"
    non_error = [r for r in result["results"] if r.get("status") != "error"]
    assert len(non_error) >= 1, "all tools errored"
    print("OK — deterministic, ≥1 tool, no crashes")


if __name__ == "__main__":
    demo()
