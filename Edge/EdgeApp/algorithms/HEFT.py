import math
from typing import Tuple

import numpy as np

from .ReversePriorityQueue import ReversePriorityQueue, ReversePriority
from ..types.DAG import DAG
from ..types.Processor import Processor


class HEFT:

    def __init__(self, dag: DAG, processors: list[Processor], bus_bandwidth: int):
        self.dag: DAG = dag
        self.processors: list[Processor] = processors
        self.bus_bandwidth: int = bus_bandwidth

        # 0: ranku, 1: start time, 2: end time, 3: processor
        self.subtask_info: list[list[int]] = [[-1, -1, -1, -1] for _ in range(len(dag.subtasks))]
        # [0: subtask_index, 1: start_time, 2: end_time]
        self.processor_allocations: list[list[list[int]]] = [[] for _ in processors]

        # calculated execution times
        self.execution_times: list[list[int]] = []
        for subtask in self.dag.subtasks:
            self.execution_times.append([p.get_execution_time(subtask.execution_cost) for p in self.processors])

    def schedule(self):
        self.calculate_ranku(0)
        scheduling_queue = ReversePriorityQueue.get()
        for i in range(len(self.subtask_info)):
            scheduling_queue.put((ReversePriority(self.subtask_info[i][0]), i))

        while not scheduling_queue.empty():
            _, i = scheduling_queue.get()
            start_time, finish_time, processor = self.eft(i)
            self.processor_allocations[processor].append([i, start_time, finish_time])
            self.subtask_info[i][1] = start_time
            self.subtask_info[i][2] = finish_time
            self.subtask_info[i][3] = processor

    def calculate_ranku(self, index: int):
        computation_avg = math.ceil(np.mean(self.execution_times[index]))

        successors: list[Tuple[int, int]] = [(edge[1], edge[2]) for edge in self.dag.edges if edge[0] == index]
        if len(successors) == 0:
            self.subtask_info[index][0] = computation_avg
        else:
            successor_ranku_max = max(self.calculate_ranku(successors[i][0]) + successors[i][1]
                                      for i in range(len(successors)))
            self.subtask_info[index][0] = computation_avg + successor_ranku_max

        return self.subtask_info[index][0]

    def eft(self, index: int) -> (int, int, int):
        start_time = np.inf
        finish_time = np.inf
        processor_index = -1
        for p in range(len(self.processors)):
            predecessors: list[Tuple[int, int]] = [(edge[0], edge[2]) for edge in self.dag.edges if edge[1] == index]
            data_available_time = 0
            for predecessor in predecessors:
                data_available_time_candidate = self.subtask_info[predecessor[0]][2]
                if p != self.subtask_info[predecessor[0]][3]:
                    data_available_time_candidate += math.ceil(predecessor[1] / self.bus_bandwidth)
                if data_available_time_candidate > data_available_time:
                    data_available_time = data_available_time_candidate

            processor_est: int = data_available_time
            if len(self.processor_allocations[p]) > 0:
                if self.processor_allocations[p][-1][2] > processor_est:
                    processor_est = self.processor_allocations[p][-1][2]

            processor_eft = processor_est + self.execution_times[index][p]
            if processor_eft < finish_time:
                start_time = processor_est
                finish_time = processor_eft
                processor_index = p

        return start_time, finish_time, processor_index

    def get_makespan(self) -> int:
        return max(
            [
                processor_allocation[-1][2] for processor_allocation in self.processor_allocations
                if len(processor_allocation) > 0
            ]
        )

    def assign_subtask_deadlines(self):
        makepsan = self.get_makespan()

        for i in range(len(self.dag.subtasks)):
            subtask = self.dag.subtasks[i]
            overhead = int((self.dag.deadline - makepsan) * (self.subtask_info[i][2] / makepsan))
            subtask.deadline = self.subtask_info[i][2] + overhead
