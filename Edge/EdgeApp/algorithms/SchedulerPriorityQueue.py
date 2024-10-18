from functools import total_ordering
from queue import PriorityQueue
from typing import Tuple

from ..types.SubTask import TaskType


@total_ordering
class SchedulerPriority:
    def __init__(self, deadline: int, task_type: TaskType):
        self.deadline = deadline
        self.task_type = task_type

    def __lt__(self, other):
        return SchedulerPriority.bigger_than(self.task_type, other.task_type, self.deadline, other.deadline)

    def __eq__(self, other):
        return self.task_type == other.task_type and self.deadline == other.deadline

    @staticmethod
    def bigger_than(task_type_1: TaskType, task_type_2: TaskType, deadline_1: int, deadline_2: int) -> bool:
        if task_type_1 == TaskType.HARD:
            if task_type_2 == TaskType.HARD:
                return deadline_1 < deadline_2
            else:
                return True
        if task_type_1 == TaskType.FIRM:
            if task_type_2 == TaskType.HARD:
                return False
            elif task_type_2 == TaskType.FIRM:
                return deadline_1 < deadline_2
            else:
                return True
        if task_type_1 == TaskType.SOFT:
            if task_type_2 == TaskType.SOFT:
                return deadline_1 < deadline_2
            else:
                return False

class SchedulerPriorityQueue:

    @staticmethod
    def get() -> PriorityQueue[Tuple[SchedulerPriority, int, int, int, int]]:
        # sorted queue based on deadline of the tasks, release time, task index, workflow index, job index
        pq: PriorityQueue[Tuple[SchedulerPriority, int, int, int, int]] = PriorityQueue()
        return pq
