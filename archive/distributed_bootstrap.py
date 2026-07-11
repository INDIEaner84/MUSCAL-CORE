from worker_node import WorkerNode
from worker_pool import DistributedScheduler, KernelMaster, WorkerPool


def start_distributed_kernel(executor):
    workers = [
        WorkerNode("A", executor),
        WorkerNode("B", executor),
        WorkerNode("C", executor),
    ]
    pool = WorkerPool(workers)
    scheduler = DistributedScheduler(pool)
    return KernelMaster(scheduler)
