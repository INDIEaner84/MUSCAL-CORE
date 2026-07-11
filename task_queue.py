import heapq


class TaskQueue:
    def __init__(self):
        self.queue = []
        self._seq = 0

    def add(self, task):
        heapq.heappush(self.queue, (task.priority, self._seq, task))
        self._seq += 1

    def get_next(self):
        if not self.queue:
            return None
        return heapq.heappop(self.queue)[2]

    def empty(self):
        return len(self.queue) == 0
