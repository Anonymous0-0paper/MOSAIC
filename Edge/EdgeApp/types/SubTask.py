from enum import Enum


class TaskType(Enum):
    HARD = "Hard",
    FIRM = "FIRM",
    SOFT = "SOFT"


class SubTask:

    def __init__(self, task_id: int, task_type: str, execution_cost: int, memory: int):
        self.id: int = task_id
        self.index: int | None = None
        self.task_type: TaskType = TaskType[task_type]
        self.execution_cost: int = execution_cost  # MI
        self.remaining_execution_cost: int = execution_cost  # MI
        self.memory: int = memory
        self.deadline: int | None = None

        self.workflow_id: int | None = -1
        self.job_id: int | None = -1
        self.absolute_deadline: int | None = None

        # 0: processor index, 1: start time, 2: end time
        self.execution_times: list[list[int]] = []
        self.arrival_time: int | None = None
        self.offload_time: int | None = None
        self.latency: int | None = None
