from functools import total_ordering
from queue import PriorityQueue
from typing import Tuple


@total_ordering
class ReversePriority:
    def __init__(self, priority):
        self.priority = priority

    def __lt__(self, other):
        return self.priority > other.priority

    def __eq__(self, other):
        return self.priority == other.priority


class ReversePriorityQueue:

    @staticmethod
    def get() -> PriorityQueue[Tuple[ReversePriority, int]]:
        pq: PriorityQueue[Tuple[ReversePriority, int]] = PriorityQueue()
        return pq
