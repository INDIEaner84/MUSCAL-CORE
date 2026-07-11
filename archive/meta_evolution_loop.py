from compiler_state import CompilerState
from compiler_updater import CompilerUpdater
from compiler_validator import CompilerValidator
from evolution_evaluator import Evaluator
from evolution_loop import Executor
from evolution_mkc import MKC
from meta_compiler import MetaCompiler
from meta_evolution_kernel import MetaEvolutionKernel


def run_meta_evolution(input_text):
    state = CompilerState()
    mkc = MKC(state)
    evaluator = Evaluator()
    meta = MetaCompiler()
    validator = CompilerValidator()
    updater = CompilerUpdater()

    kernel = MetaEvolutionKernel(state, mkc, evaluator, meta, validator, updater)
    executor = Executor()
    return kernel.run(input_text, executor)


_persistent_state = CompilerState()
_persistent_mkc = MKC(_persistent_state)
_persistent_evaluator = Evaluator()
_persistent_meta = MetaCompiler()
_persistent_validator = CompilerValidator()
_persistent_updater = CompilerUpdater()
_persistent_kernel = MetaEvolutionKernel(
    _persistent_state, _persistent_mkc, _persistent_evaluator,
    _persistent_meta, _persistent_validator, _persistent_updater
)
_persistent_executor = Executor()


def run_persistent(input_text):
    return _persistent_kernel.run(input_text, _persistent_executor)
