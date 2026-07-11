class Task:
    def __init__(self, tool, args, priority=1):
        self.tool = tool
        self.args = args
        self.priority = priority
        self.status = "pending"
