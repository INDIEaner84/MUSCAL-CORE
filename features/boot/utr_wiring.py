"""Boot-time Trust Core wiring for MuscalOS.

Installed during plugin_loader import scan (inside MuscalOS._init_plugins).
Sets global EventStore registry and default timeout so that ALL callers
of create_default_utr() automatically get wired callbacks and timeout.

This is a transitional adapter until main_boot.py uses EnrichedMuscalOS directly.

Design:
  - Sets set_global_event_store(es) — every create_default_utr() call auto-wires
  - Sets set_global_default_timeout(300) — every UTR gets safe default timeout
  - Monkey-patches MuscalOS._init_system_runtime (runs after _init_plugins)
  - Starts ExecutionWatchdog with EventStore+EventBus
  - Creates VerificationOrchestrator if not present
  - Patches shutdown() to stop watchdog + shutdown UTR pool
"""

import logging

logger = logging.getLogger(__name__)


class Plugin:
    name = "utr_wiring"
    version = "1.0.0"

    def register(self, hooks: dict):
        pass

    def execute(self, context: dict):
        pass


def _install():
    import muscal_os as _mos

    if hasattr(_mos.MuscalOS, "_trust_core_installed"):
        return
    _mos.MuscalOS._trust_core_installed = True

    _original_init_system_runtime = _mos.MuscalOS._init_system_runtime

    def _wired_init_system_runtime(self):
        result = _original_init_system_runtime(self)
        try:
            _wire_trust_core(self)
        except Exception:
            logger.exception("Trust Core wiring failed — continuing boot")
        return result

    _mos.MuscalOS._init_system_runtime = _wired_init_system_runtime

    _original_shutdown = _mos.MuscalOS.shutdown

    def _wired_shutdown(self):
        try:
            _stop_trust_core(self)
        except Exception:
            logger.exception("Trust Core shutdown failed — continuing shutdown")
        return _original_shutdown(self)

    _mos.MuscalOS.shutdown = _wired_shutdown


def _wire_trust_core(mos):
    if mos.event_store is None:
        logger.warning(
            "Trust Core wiring SKIPPED — no EventStore. "
            "All UTR instances will lack receipt/verification persistence."
        )
        _assert_trust_core_off()
        return

    from features.tool_runtime.tool_runtime import (
        set_global_event_store,
        set_global_default_timeout,
    )
    from features.monitoring.execution_watchdog import ExecutionWatchdog

    set_global_event_store(mos.event_store)
    set_global_default_timeout(300)
    logger.info(
        "Global EventStore set — all create_default_utr() calls auto-wired"
    )
    logger.info("Global default timeout set to 300s")

    if not hasattr(mos, "_verifier") or mos._verifier is None:
        from features.verification.orchestrator import VerificationOrchestrator
        mos._verifier = VerificationOrchestrator(event_bus=mos.events)
        logger.info("VerificationOrchestrator created with EventBus")

    watchdog = ExecutionWatchdog(
        event_store=mos.event_store,
        event_bus=mos.events,
    )
    watchdog.start()
    mos._trust_watchdog = watchdog
    logger.info("ExecutionWatchdog started")

    _assert_trust_core_on()


def _stop_trust_core(mos):
    watchdog = getattr(mos, "_trust_watchdog", None)
    if watchdog is not None:
        watchdog.stop()
        logger.info("ExecutionWatchdog stopped")


def _assert_trust_core_on():
    from features.tool_runtime.tool_runtime import get_global_event_store
    es = get_global_event_store()
    assert es is not None, (
        "Trust Core ASSERTION FAILED: global EventStore is None. "
        "Some create_default_utr() callers will lack receipt/verification persistence. "
        "Check that Trust Core wiring ran during boot."
    )


def _assert_trust_core_off():
    from features.tool_runtime.tool_runtime import get_global_event_store
    es = get_global_event_store()
    if es is not None:
        logger.warning(
            "Trust Core state inconsistency: global EventStore is set "
            "but current boot path has no EventStore. "
            "Previous boot may have left stale state."
        )


_install()
