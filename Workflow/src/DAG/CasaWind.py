import math
import random

import numpy as np

from Workflow.src.DAG.DAG import DAG, DAGMode
from Workflow.src.DAG.DAGSubTask import DAGSubTask
from Workflow.src.SubTask import TaskType


class CaseWind:

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

        level_1 = (dag_size - 9 - 2) // 3
        level_2 = (dag_size - 9) - (level_1 * 3)

        for i in range(level_1):
            edges.append([i, level_1 + i, 0])
            edges.append([level_1 + i, level_1 * 2 + i, 0])
            edges.append([level_1 * 2 + i, level_1 * 3, 0])

        edges.append([level_1 * 3, level_1 * 3 + 2, 0])
        edges.append([level_1 * 3 + 1, level_1 * 3 + 3, 0])
        edges.append([level_1 * 3 + 2, level_1 * 3 + 3, 0])
        edges.append([level_1 * 3 + 2, level_1 * 3 + 4, 0])
        edges.append([level_1 * 3 + 3, level_1 * 3 + 5, 0])
        edges.append([level_1 * 3 + 4, level_1 * 3 + 6, 0])
        edges.append([level_1 * 3 + 6, level_1 * 3 + 7 + level_2, 0])

        for i in range(level_2):
            edges.append([level_1 * 3 + 7 + i, level_1 * 3 + 7 + level_2, 0])

        edges.append([level_1 * 3 + 7 + level_2, level_1 * 3 + 8 + level_2, 0])

        dag = DAG(DAGMode.CasaWind, dag_id, tasks, edges)
        dag.add_dummy_entry()
        dag.generate_deadline(deadline_min, deadline_max)
        dag.generate_arrival_time(arrival_scale)
        dag.generate_communication_data_sizes(communication_min, communication_max)
        return dag