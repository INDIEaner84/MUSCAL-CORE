#!/usr/bin/env python3
import argparse
import json
import os
import signal
import sys
import time
from typing import Any, Dict

from chat_compiler import ChatFolderCompiler
from graph_memory import GraphMemory
from mcxf_fusion import get_memory_context, init_fusion
from mkc import mkc as mkc_compile
from muscal_loop import MuscalLoop
from muscal_os import MuscalOS
from os_config import load_config
from trace_engine import print_trace


def parse_args():
    parser = argparse.ArgumentParser(description="MUSCAL OS Bootstrap v0.1")
    parser.add_argument("--mode", "-m", choices=["local_dev", "production", "simulation"],
                        default="local_dev", help="Deployment mode")
    parser.add_argument("--no-graph", action="store_true", help="Disable graph layer")
    parser.add_argument("--no-sphere", action="store_true", help="Disable sphere UI layer")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    parser.add_argument("--command", "-c", type=str, help="Single command mode (non-interactive)")
    parser.add_argument("--eval", "-e", type=str, help="Evaluate input and exit")
    parser.add_argument("--status", action="store_true", help="Show status and exit")
    parser.add_argument("--loop", action="store_true", help="Run LLM-driven autonomous loop")
    parser.add_argument("--ollama", action="store_true", help="Use real Ollama LLM in loop")
    parser.add_argument("--trace", action="store_true", help="Print execution trace after loop")
    parser.add_argument("--compile", type=str, metavar="PATH",
                        help="Compile all .txt files in folder to MCXF")
    parser.add_argument("--sql", type=str, metavar="DB", default=None,
                        help="Enable SQLite persistence (path to .db file)")
    parser.add_argument("--dashboard", action="store_true",
                        help="Launch Streamlit dashboard")
    parser.add_argument("--max-iterations", type=int, default=5,
                        help="Max loop iterations (default: 5)")
    return parser.parse_args()


def print_banner(os_obj: MuscalOS):
    cfg = os_obj.config
    print("=" * 54)
    print(f"  MUSCAL OS v0.1  |  Mode: {cfg.mode.value.upper()}")
    print(f"  Graph: {'ON' if cfg.enable_graph else 'OFF'}  "
          f"Sphere: {'ON' if cfg.enable_sphere else 'OFF'}  "
          f"Sim: {'ON' if cfg.simulation_mode else 'OFF'}")
    print("=" * 54)


def print_boot_report(os_obj: MuscalOS):
    report = os_obj._boot_report
    if not report:
        return
    print(f"  Boot: {report.summary}")
    for s in report.steps:
        icon = "+" if s.success else "!"
        print(f"    [{icon}] {s.phase.value}.{s.step_name}  ({s.duration:.3f}s)"
              + (f"  ERROR: {s.error}" if s.error else ""))
    print()


def print_status(os_obj: MuscalOS):
    s = os_obj.get_status()
    print(f"  Running : {s['running']}")
    print(f"  Uptime  : {s['uptime']:.1f}s")
    print(f"  Mode    : {s['mode']}")
    print(f"  Sim     : {s['simulation']}")
    print(f"  Boot    : {s['boot']}")
    print(f"  Events  : {s['events'].get('total_events', 0)} published, "
          f"{s['events'].get('subscriber_count', 0)} subscribers")
    print(f"  Kernel  : {'ready' if s['kernel_ready'] else 'not loaded'}")
    print()


def run_interactive(os_obj: MuscalOS):
    print("  Enter input (or /help, /status, /shutdown)")
    while os_obj._running:
        try:
            user_input = input(">>> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        cmd = user_input.strip().lower()
        if cmd == "/shutdown" or cmd == "/exit" or cmd == "/quit":
            break
        elif cmd == "/help":
            print("  Commands:")
            print("    /help          Show this help")
            print("    /status        Show OS status")
            print("    /compile PATH  Compile .txt folder to MCXF")
            print("    /rag QUERY     Search memory context")
            print("    /shutdown      Shutdown and exit")
            continue
        elif cmd.startswith("/compile "):
            path = cmd[len("/compile "):].strip()
            run_compile(os_obj, path)
            continue
        elif cmd.startswith("/rag "):
            query = cmd[len("/rag "):].strip()
            ctx = get_memory_context(query)
            print("  COSINE:")
            for r in ctx.get("cosine", []):
                print(f"    score={r.get('score','?')} text={r.get('text','')[:80]}")
            graph_hits = ctx.get("graph", [])
            if graph_hits:
                print("  GRAPH:")
                for r in graph_hits:
                    print(f"    node={r.get('node','?')[:8]} relations={len(r.get('relations',[]))}")
            continue
        elif cmd == "/status":
            print_status(os_obj)
            continue
        elif not cmd:
            continue

        result = os_obj.run(user_input)
        mcxf = result.get("mcxf", {})
        diff = result.get("diff", {})
        vs = result.get("validation_status", "UNKNOWN")
        print(f"  VALIDATION: {vs}  |  RECOMMENDATION: {diff.get('recommendation', 'N/A')}")
        print(f"  MCXF      : {len(mcxf.get('decisions',[]))}d {len(mcxf.get('tasks',[]))}t "
              f"{len(mcxf.get('open_questions',[]))}q")
        print(f"  EXECUTION : {result.get('execution', [])}")
        print(f"  SUCCESS   : {result.get('success', False)}")
        if result.get("feedback") and result["feedback"] != "no issues detected":
            print(f"  FEEDBACK  : {result['feedback']}")
        if result.get("errors"):
            print(f"  ERRORS    : {result['errors']}")
        if result.get("simulation"):
            print("  [SIMULATION] No side effects were executed.")
        print()


def run_single_command(os_obj: MuscalOS, command: str):
    result = os_obj.run(command)
    print(json.dumps(result, indent=2, default=str))


def run_loop(os_obj: MuscalOS, use_ollama: bool = False, trace: bool = False):
    print("  MUSCAL Autonomous Loop  |  Model: qwen2.5:7b-instruct")
    print("  Enter task (or /help, /status, /shutdown)")
    while os_obj._running:
        try:
            user_input = input(">>> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break

        cmd = user_input.strip().lower()
        if cmd == "/shutdown" or cmd == "/exit" or cmd == "/quit":
            break
        elif cmd == "/help":
            print("  Commands:")
            print("    /help          Show this help")
            print("    /status        Show OS status")
            print("    /compile PATH  Compile .txt folder to MCXF")
            print("    /rag QUERY     Search memory context")
            print("    /shutdown      Shutdown and exit")
            print("    raw text       Run LLM loop on input")
            continue
        elif cmd.startswith("/compile "):
            path = cmd[len("/compile "):].strip()
            run_compile(os_obj, path)
            continue
        elif cmd.startswith("/rag "):
            query = cmd[len("/rag "):].strip()
            ctx = get_memory_context(query)
            print("  COSINE:")
            for r in ctx.get("cosine", []):
                print(f"    score={r.get('score','?')} text={r.get('text','')[:80]}")
            graph_hits = ctx.get("graph", [])
            if graph_hits:
                print("  GRAPH:")
                for r in graph_hits:
                    print(f"    node={r.get('node','?')[:8]} relations={len(r.get('relations',[]))}")
            continue
        elif cmd == "/status":
            print_status(os_obj)
            continue
        elif not cmd:
            continue

        loop = MuscalLoop(use_ollama=use_ollama)
        result = loop.run(user_input)

        print(f"\n  Iterations     : {result['iterations']}")
        print(f"  Tasks executed : {result['tasks_executed']}")
        for h in result["history"]:
            print(f"  --- Iteration {h['iteration']} ---")
            print(f"  MCXF   : {json.dumps(h['mcxf'])}")
            for r in h["results"]:
                status = r.get("status", r.get("printed", "?"))
                print(f"  Result : {r['tool']} -> {status}")
        if trace:
            print_trace()
        print()
    os_obj.shutdown()


def run_compile(os_obj: MuscalOS, folder_path: str):
    if not os.path.isdir(folder_path):
        print(f"  ERROR: folder not found: {folder_path}")
        return
    compiler = ChatFolderCompiler(mkc_compile)
    result = compiler.compile_all(folder_path)
    print(f"\n  Compiled {result['count']} files from {folder_path}\n")
    for doc in result["documents"]:
        print(f"  [{doc['source']}]")
        print(f"    decisions: {len(doc['mcxf'].get('decisions', []))}")
        print(f"    tasks    : {len(doc['mcxf'].get('tasks', []))}")
        print(f"    arch     : {len(doc['mcxf'].get('architecture', []))}")
    print(f"\n  Full output:\n{json.dumps(result, indent=2, default=str)}")


def main():
    args = parse_args()

    overrides = {}
    if args.no_graph:
        overrides["enable_graph"] = False
    if args.no_sphere:
        overrides["enable_sphere"] = False
    if args.verbose:
        overrides["verbose_logging"] = True

    config = load_config(mode=args.mode, overrides=overrides)
    os_obj = MuscalOS(config=config)

    def handle_signal(sig, frame):
        print("\n  Shutting down...")
        os_obj.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    report = os_obj.start()
    print_banner(os_obj)
    print_boot_report(os_obj)

    if not report.success:
        print(f"  Boot FAILED: {report.errors}")
        sys.exit(1)

    init_fusion(graph=GraphMemory(), sql_path=args.sql)

    if args.dashboard:
        print("  Launching dashboard...")
        import subprocess
        subprocess.Popen([sys.executable, "-m", "streamlit", "run",
                          os.path.join(os.path.dirname(__file__), "dashboard.py")])
        print("  Dashboard starting at http://localhost:8501")

    if args.status:
        print_status(os_obj)
        os_obj.shutdown()
        sys.exit(0)

    if args.eval:
        run_single_command(os_obj, args.eval)
        os_obj.shutdown()
        sys.exit(0)

    if args.command:
        run_single_command(os_obj, args.command)
        os_obj.shutdown()
        sys.exit(0)

    if args.compile:
        run_compile(os_obj, args.compile)
        os_obj.shutdown()
        sys.exit(0)

    if args.loop:
        run_loop(os_obj, use_ollama=args.ollama, trace=args.trace)
    else:
        run_interactive(os_obj)
    os_obj.shutdown()
    print("  Goodbye.")


if __name__ == "__main__":
    main()
