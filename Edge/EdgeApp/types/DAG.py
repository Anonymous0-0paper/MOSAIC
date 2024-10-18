from enum import Enum

from .DAGSubTask import DAGSubTask
from ..dtos import DagSerializer


class DAGMode(Enum):
    GE = "GE",
    FFT = "FFT",
    FullyTopology = "FullyTopology"


class DAG:

    def __init__(self, dto: DagSerializer):
        self.id: int = dto['id']
        self.deadline: int = dto['deadline']
        self.arrival_time: int = dto['arrivalTime']
        self.edges: list[list[int]] = dto['edges']
        self.subtasks: list[DAGSubTask] = []
        for subtask in dto['subtasks']:
            self.subtasks.append(DAGSubTask(self.id, subtask))
