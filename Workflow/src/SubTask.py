import random
from enum import Enum


class TaskType(Enum):
    HARD = "Hard",
    FIRM = "FIRM",
    SOFT = "SOFT"


class SubTask:

    def __init__(self, task_id: int, task_type: TaskType):
        self.id: int = task_id
        self.task_type: TaskType = task_type
        self.execution_cost: int | None = None  # MI
        self.memory: int | None = None

    def generate_memory(self, memory_min: int, memory_max: int):
        self.memory = random.randint(memory_min, memory_max)

    def generate_execution_cost(self, execution_min: int, execution_max: int):
        self.execution_cost = random.randint(execution_min, execution_max)
