class WorkerPool:
    def __init__(self, workers):
        self.workers = workers

    def get_free_worker(self):
        for w in self.workers:
            if not w.busy:
                return w
        return None


class DistributedScheduler:
    def __init__(self, worker_pool):
        self.pool = worker_pool

    def run(self, tasks):
        results = []
        for task in tasks:
            worker = None
            while worker is None:
                worker = self.pool.get_free_worker()
            result = worker.execute(task)
            results.append(result)
        return results


class KernelMaster:
    def __init__(self, scheduler):
        self.scheduler = scheduler

    def run(self, mcxf_tasks):
        return self.scheduler.run(mcxf_tasks)
