import logging
import os
import signal
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("supervisor")

_shutdown_requested = False


def _handle_sigterm(signum, frame):
    global _shutdown_requested
    _shutdown_requested = True
    log.info("SIGTERM received — initiating graceful shutdown")


def start():
    signal.signal(signal.SIGTERM, _handle_sigterm)
    signal.signal(signal.SIGINT, _handle_sigterm)

    os.makedirs("storage", exist_ok=True)

    log.info("=== MUSCAL CORE Supervisor v0.1 ===")

    # Phase 1: MUSCAL OS boot
    log.info("Phase 1: Booting MUSCAL OS...")
    from muscal_os import MuscalOS
    os_instance = MuscalOS()
    boot_report = os_instance.start()
    if not boot_report.success:
        log.error("OS boot failed: %s", boot_report.summary)
        sys.exit(1)
    log.info("OS ready: %s", boot_report.summary)

    if _shutdown_requested:
        os_instance.shutdown()
        return

    # Phase 2: API Runtime boot
    log.info("Phase 2: Starting API Runtime...")
    from runtime.api import create_app as _create_app
    from runtime.api import set_globals, set_server_ready
    from runtime.api import register_blueprints, init_app
    from runtime.database import check_consistency_on_start, init_db
    from runtime.kernel.bootstrap import bootstrap_kernel, detect_bootstrap_needed
    from runtime.kernel.governance import GovernanceSync
    from runtime.kernel.scheduler import RoutingPolicy
    from runtime.kernel.writer import WriterThread
    from runtime.llm.models import init_router, init_smol
    from runtime.observation.loop import ObservationLoop, set_governance
    import config

    init_db()
    check_consistency_on_start()

    writer = WriterThread()
    writer.start()

    if detect_bootstrap_needed():
        bootstrap_kernel(writer)

    policy = RoutingPolicy()
    governance = GovernanceSync()
    set_governance(governance)

    if not init_router():
        log.warning("Qwen router not available")
    if not init_smol():
        log.warning("SMOL not available")

    obs_loop = ObservationLoop(writer)
    obs_loop.start()

    app = _create_app()
    set_globals(writer=writer, obs_loop=obs_loop, policy=policy, governance=governance)
    set_server_ready(True)

    log.info("All systems ready. Flask on :%d", config.RUNTIME_FLASK_PORT)

    # Phase 3: Block on Flask, with shutdown check
    try:
        app.run(host="0.0.0.0", port=config.RUNTIME_FLASK_PORT, debug=False, threaded=True)
    finally:
        _shutdown_requested = True

    # Phase 4: Graceful shutdown
    log.info("Shutting down...")
    set_server_ready(False)
    os_instance.shutdown()
    obs_loop.stop()
    writer.stop()
    log.info("Shutdown complete.")


if __name__ == "__main__":
    start()
