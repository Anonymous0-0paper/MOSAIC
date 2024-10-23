import math
import random

import numpy as np

from Workflow.src.DAG.DAG import DAG, DAGMode
from Workflow.src.DAG.DAGSubTask import DAGSubTask
from Workflow.src.SubTask import TaskType


class Montage:

    @staticmethod
    def generate_dag(dag_id: int, dag_size: int, task_type: TaskType, arrival_scale: float,
                     memory_min: int, memory_max: int, execution_min: int, execution_max: int,
                     deadline_min: int, deadline_max: int, communication_min: int, communication_max: int) -> DAG:

        # generate tasks
        tasks: np.array(DAGSubTask) = []
        for task_id in range(dag_size):
            task = DAGSubTask.generate(dag_id, task_id, task_type, memory_min, memory_max,
                                       execution_min, execution_max)
            tasks.append(task)

        # generate communication
        edges: list[list[int]] = []

        level_1 = dag_size // 5
        level_2 = level_1 + level_1 // 2
        level_5 = dag_size - level_1 - level_2 - 6

        for i in range(level_1):
            predecessors = []
            for k in range(random.randint(1, 4)):
                predecessor = random.randint(level_1, level_1 + level_2 - 1)
                if predecessor not in predecessors:
                    predecessors.append(predecessor)

            for k in predecessors:
                edges.append([i, k, 0])

        for i in range(level_2):
            edges.append([level_1 + i, level_1 + level_2, 0])

        edges.append([level_1 + level_2, level_1 + level_2 + 1, 0])

        for i in range(level_5):
            edges.append([level_1 + level_2 + 1, level_1 + level_2 + 2 + i, 0])
            edges.append([level_1 + level_2 + 2 + i, level_1 + level_2 + 2 + level_5, 0])

        edges.append([level_1 + level_2 + 2 + level_5, level_1 + level_2 + 3 + level_5, 0])
        edges.append([level_1 + level_2 + 3 + level_5, level_1 + level_2 + 4 + level_5, 0])
        edges.append([level_1 + level_2 + 4 + level_5, level_1 + level_2 + 5 + level_5, 0])

        dag = DAG(DAGMode.FFT, dag_id, tasks, edges)
        dag.add_dummy_entry()
        dag.generate_deadline(deadline_min, deadline_max)
        dag.generate_arrival_time(arrival_scale)
        dag.generate_communication_data_sizes(communication_min, communication_max)
        return dag

    @staticmethod
    def get_m(dag_size: int) -> int:
        for m_log2 in range(1, dag_size):
            m = int(math.pow(2, m_log2))
            tasks_count = int(m * m_log2 + 2 * m - 1)
            if tasks_count >= dag_size:
                return m
