from minimal_core import Executor
from minimal_evaluator import Evaluator
from minimal_feedback import FeedbackMemory
from minimal_fusion import run_fusion
from minimal_mcxf_memory import MCXFMemory
from minimal_memory import Memory
from minimal_mkc import MKC
from minimal_rag import RAGStore
from minimal_router import DispatchEngine

if __name__ == "__main__":
    rag = RAGStore()
    mcxf_mem = MCXFMemory()

    mkc = MKC()
    executor = Executor()
    dispatch = DispatchEngine(executor)

    evaluator = Evaluator()
    feedback_mem = FeedbackMemory()

    while True:
        user = input(">> ")
        out = run_fusion(
            user,
            rag,
            mkc,
            executor,
            dispatch,
            memory=None,
            evaluator=evaluator,
            feedback_mem=feedback_mem,
            mcxf_mem=mcxf_mem,
        )
        print(out)
