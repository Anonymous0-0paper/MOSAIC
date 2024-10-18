from .SubTask import SubTask


class PeriodicTask(SubTask):
    def __init__(self, task_id: int, job_index: int, task_type: str, execution_cost: int, memory: int, deadline: int):
        super().__init__(task_id, task_type, execution_cost, memory)
        self.deadline = deadline
        self.period = deadline
        self.job_index = job_index
        self.job_id = job_index
