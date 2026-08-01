import logging

import config
from runtime.monitoring.logging import setup_logging

setup_logging()
log = logging.getLogger("muscal.main")


def main() -> None:
    from runtime.api import init_app, register_blueprints, set_globals, set_server_ready
    from runtime.database import check_consistency_on_start, init_db
    from runtime.event_store import EventStore
    from runtime.kernel.bootstrap import bootstrap_kernel, detect_bootstrap_needed
    from runtime.kernel.governance import GovernanceSync
    from runtime.kernel.scheduler import RoutingPolicy
    from runtime.kernel.writer import WriterThread
    from runtime.llm.models import init_router, init_smol
    from runtime.observation.loop import ObservationLoop, set_governance

    log.info("=== MUSCAL CORE Runtime v0.1 ===")
    log.info("Session: %s", config.SESSION_ID)
    log.info("DB: %s", config.DB_PATH)

    init_db(config.DB_PATH)
    check_consistency_on_start(config.DB_PATH)

    event_store = EventStore(config.DB_PATH)
    writer = WriterThread(config.DB_PATH, event_store=event_store)
    writer.start()

    if detect_bootstrap_needed(config.DB_PATH):
        bootstrap_kernel(writer)

    policy = RoutingPolicy(config.DB_PATH)

    governance = GovernanceSync()
    log.info("Governance initialized (max_iterations=%d)", governance.limits.max_iterations)

    if not init_router():
        log.warning("Qwen router not available \u2014 check Ollama")
    if not init_smol():
        log.warning("SMOL not available \u2014 simple chat fallback")

    set_governance(governance)
    obs_loop = ObservationLoop(writer, config.DB_PATH)
    obs_loop.start()

    from runtime.api import create_app as _create_app
    app = _create_app()

    set_globals(writer=writer, obs_loop=obs_loop, policy=policy, governance=governance)
    set_server_ready(True)

    log.info("All systems running. Flask on :%d", config.RUNTIME_FLASK_PORT)

    try:
        app.run(host="0.0.0.0", port=config.RUNTIME_FLASK_PORT, debug=False, threaded=True)
    finally:
        log.info("Shutting down...")
        obs_loop.stop()
        writer.stop()
        log.info("Shutdown complete.")


if __name__ == "__main__":
    main()
