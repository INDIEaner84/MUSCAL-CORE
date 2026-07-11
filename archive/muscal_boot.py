"""
⚠️ DEPRECATED — Uses deprecated `kernel_core.Kernel`.
    Use `main_boot.py` (MuscalOS) or `main.py` (MuscalKernel REPL) instead.
"""
from kernel_core import Kernel


class MUSCAL_OS:
    """⚠️ DEPRECATED — Use `MuscalOS` from `muscal_os.py` instead."""

    def __init__(self):
        self.kernel = Kernel()

    def boot(self):
        print("[BOOT] Initializing MUSCAL OS...")
        self.kernel.initialize()
        self.kernel.run()


if __name__ == "__main__":
    os = MUSCAL_OS()
    os.boot()
