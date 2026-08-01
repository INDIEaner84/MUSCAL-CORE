# MUSCAL Runtime Foundation v1.0

## 1. Purpose

The Runtime Foundation layer provides the process lifecycle management and
inter-process communication infrastructure for the MUSCAL multi-agent system.
It operates below the kernel abstraction and above the operating system,
enabling agent spawning, monitoring, IPC, and daemon orchestration without
direct kernel coupling.

## 2. Architecture

```
+--------------------------------------------------+
|                 MUSCALDaemon                      |
|  Orchestrates IPC + ProcessManager + Signals      |
|  +------------------+  +------------------------+ |
|  |    IPCServer     |  |    ProcessManager      | |
|  |  Unix/TCP Socket |  |  Agent Lifecycle       | |
|  |  JSON Lines      |  |  Spawn / Kill / Restart| |
|  |  Handler Dispatch|  |  Heartbeat / Monitor   | |
|  +--------+---------+  +----------+-------------+ |
|           |                       |               |
|           v                       v               |
|    +-----------+          +--------------+        |
|    | IPCClient |          | ManagedAgent |        |
|    | Auto-     |          | State Machine|        |
|    | Reconnect |          | STARTING     |        |
|    | Event Sub |          | RUNNING      |        |
|    +-----------+          | STOPPING     |        |
|                           | STOPPED      |        |
|                           | CRASHED      |        |
|                           +--------------+        |
+--------------------------------------------------+
         |                          |
         v                          v
    config.py                 interfaces.py
    (env vars)                (protocols)
```

## 3. Components

### ProcessManager (runtime/process_manager.py)

Manages child-agent process lifecycle:

- **spawn_agent**: Creates a subprocess with isolated environment, tracks PID,
  state, restart count, and heartbeat.
- **shutdown_agent**: Graceful termination with SIGTERM, falls back to SIGKILL
  after timeout.
- **restart_agent**: Re-spawns agent while preserving restart count. Exceeds
  `MUSCAL_MAX_AGENT_RESTARTS` → state becomes CRASHED.
- **monitor_loop**: Background task polling agent processes for crashes
  (returncode != None) and heartbeat timeouts every 5 seconds.
- **AgentState enum**: STARTING → RUNNING → STOPPING → STOPPED | CRASHED.

### IPCServer (runtime/ipc_server.py)

Async IPC server using JSON Lines protocol:

- **Unix socket** (default) or **TCP** fallback — configurable via `use_unix`.
- **Handler dispatch** by message type — callers register coroutine handlers.
- **Connection tracking** via `connected_clients` property.
- **broadcast** — sends message to all connected clients.
- Socket files cleaned up on `stop()`.

### IPCClient (runtime/ipc_client.py)

Client SDK for daemon communication:

- **Auto-reconnect** on connection loss during `send()`.
- **Response queue** with configurable timeout (`MUSCAL_IPC_TIMEOUT`).
- **Event subscriptions** via `on_event()` with wildcard pattern matching.
- Convenience methods: `register()`, `emit_event()`, `submit_task()`,
  `heartbeat()`.

### MUSCALDaemon (runtime/daemon.py)

Orchestrator that owns IPC server and process manager:

- **start()**: Initializes IPC server, process manager monitor, signal handlers.
- **stop()**: Gracefully shuts down all agents, stops monitor, stops IPC server,
  cleans up PID file.
- **request_shutdown()**: Sets shutdown event for `wait_for_shutdown()`.
- **IPC handlers**: daemon.spawn, daemon.kill, heartbeat, daemon.status.
- **Signal handlers**: SIGTERM and SIGINT trigger graceful shutdown.

## 4. Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `MUSCAL_SOCKET_PATH` | `BASE_DIR/runtime.sock` | Unix socket path |
| `MUSCAL_TCP_HOST` | `127.0.0.1` | TCP fallback host |
| `MUSCAL_TCP_PORT` | `0` (ephemeral) | TCP fallback port |
| `MUSCAL_DAEMON_MODE` | `auto` | Daemon operating mode |
| `MUSCAL_MAX_AGENT_RESTARTS` | `3` | Max restart attempts per agent |
| `MUSCAL_IPC_TIMEOUT` | `30.0` | IPC response timeout (seconds) |

## 5. Protocols (interfaces.py)

- **ProcessManagerProvider**: spawn_agent, shutdown_agent, shutdown_all,
  get_agent_pid, list_agents, get_status.
- **IPCServerProvider**: start, stop, broadcast, is_running, connected_clients.
- **IPCClientProvider**: connect, disconnect, send, is_connected.
- **DaemonProvider**: start, stop, is_running, get_uptime.

## 6. Boundaries

- **No kernel imports**: Runtime modules import only `config.py` and
  `interfaces.py` from MUSCAL internals.
- **No event_bus coupling**: Event subscription is client-side via IPC;
  server-side handler stubs return structured dicts.
- **No Governance coupling**: Iteration limits and policy checks deferred to
  Phase 2.
- **No frozen file modifications**: All new code lives in `runtime/` or `tests/`.
