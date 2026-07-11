import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class BootPhase(Enum):
    INIT = "INIT"
    LOAD_CONFIG = "LOAD_CONFIG"
    INIT_MODULES = "INIT_MODULES"
    START_SERVICES = "START_SERVICES"
    HEALTH_CHECK = "HEALTH_CHECK"
    READY = "READY"
    SHUTDOWN = "SHUTDOWN"
    FAILED = "FAILED"


@dataclass
class BootStepResult:
    phase: BootPhase
    step_name: str
    success: bool
    duration: float = 0.0
    error: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BootReport:
    total_duration: float = 0.0
    steps: List[BootStepResult] = field(default_factory=list)
    final_phase: BootPhase = BootPhase.INIT
    success: bool = False
    errors: List[str] = field(default_factory=list)

    @property
    def summary(self) -> str:
        phase = self.final_phase.value
        status = "OK" if self.success else "FAILED"
        return f"[{status}] {phase} in {self.total_duration:.2f}s ({len(self.steps)} steps, {len(self.errors)} errors)"


class BootManager:
    def __init__(self):
        self.phase: BootPhase = BootPhase.INIT
        self.steps: List[BootStepResult] = []
        self._hooks: Dict[BootPhase, List[Callable]] = {p: [] for p in BootPhase}

    def on_phase(self, phase: BootPhase, hook: Callable) -> None:
        self._hooks[phase].append(hook)

    def run_phase(self, phase: BootPhase,
                  steps: List[tuple]) -> bool:
        self.phase = phase
        phase_ok = True
        for step_name, step_fn in steps:
            t0 = time.time()
            try:
                result = step_fn()
                dur = time.time() - t0
                ok = result if isinstance(result, bool) else True
                self.steps.append(BootStepResult(
                    phase=phase, step_name=step_name,
                    success=ok, duration=dur, details={"result": str(result)}
                ))
                if not ok:
                    phase_ok = False
                    self.steps[-1].error = f"{step_name} returned False"
            except Exception as e:
                dur = time.time() - t0
                phase_ok = False
                self.steps.append(BootStepResult(
                    phase=phase, step_name=step_name,
                    success=False, duration=dur, error=str(e)
                ))
        for hook in self._hooks.get(phase, []):
            try:
                hook(self)
            except Exception:
                pass
        if not phase_ok:
            self.phase = BootPhase.FAILED
        return phase_ok

    def get_report(self) -> BootReport:
        total = sum(s.duration for s in self.steps)
        errors = [f"{s.phase.value}.{s.step_name}: {s.error}" for s in self.steps if not s.success]
        no_errors = len(errors) == 0
        return BootReport(
            total_duration=total,
            steps=list(self.steps),
            final_phase=self.phase,
            success=no_errors and self.phase in (BootPhase.READY, BootPhase.SHUTDOWN),
            errors=errors,
        )

    def reset(self) -> None:
        self.phase = BootPhase.INIT
        self.steps.clear()
