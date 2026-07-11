import signal
import time


class TimeoutExpired(Exception):
    pass


class ResourceWatchdog:
    def __init__(self, max_cpu_ms=5000):
        self.max_cpu_ms = max_cpu_ms
        self._active = False
        self._has_alarm = hasattr(signal, 'SIGALRM')

    def start(self):
        if self._has_alarm:
            signal.signal(signal.SIGALRM, self._timeout_handler)
            signal.setitimer(signal.ITIMER_REAL, self.max_cpu_ms / 1000.0)
        self._active = True

    def stop(self):
        if self._has_alarm and self._active:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, signal.SIG_DFL)
        self._active = False

    def cancel(self):
        self.stop()

    @staticmethod
    def _timeout_handler(signum, frame):
        raise TimeoutExpired("Plugin exceeded CPU time limit")
