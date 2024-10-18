from enum import Enum

from ..types.Edge import Edge


class TaskType(Enum):
    HARD = "Hard",
    FIRM = "FIRM",
    SOFT = "SOFT"


class SubTask:

    def __init__(self, edge: Edge, task_id: int, workflow_id: int, job_id: int, task_type: str, execution_cost: int,
                 memory: int, absolute_deadline: int):
        self.edge: Edge = edge
        self.id: int = task_id
        self.workflow_id: int = workflow_id
        self.job_id: int = job_id
        self.index: int | None = None
        self.absolute_deadline: int | None = None
        self.arrival_time: int | None = None
        self.task_type: TaskType = TaskType[task_type]
        self.execution_cost: int = execution_cost  # MI
        self.remaining_execution_cost: int = execution_cost  # MI
        self.memory: int = memory
        self.absolute_deadline_time: float = absolute_deadline

        # 0: processor index, 1: start time, 2: end time
        self.execution_times: list[list[int]] = []
        self.temp_execution_times: list[list[int]] = []
        self.temp_remaining_execution_cost = execution_cost

        self.is_notify = False

    def clear_cache(self):
        self.temp_execution_times = [item for item in self.execution_times]
        self.temp_remaining_execution_cost = self.remaining_execution_cost

    def apply_cache(self):
        self.execution_times = [item for item in self.temp_execution_times]
        self.remaining_execution_cost = self.temp_remaining_execution_cost
