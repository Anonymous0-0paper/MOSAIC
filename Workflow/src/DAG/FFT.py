import math

import numpy as np

from Workflow.src.DAG.DAG import DAG, DAGMode
from Workflow.src.DAG.DAGSubTask import DAGSubTask
from Workflow.src.SubTask import TaskType


class FFT:

    @staticmethod
    def generate_dag(dag_id: int, dag_size: int, task_type: TaskType, arrival_scale: float,
                     memory_min: int, memory_max: int, execution_min: int, execution_max: int,
                     deadline_min: int, deadline_max: int, communication_min: int, communication_max: int) -> DAG:

        # compute m of FFT DAG
        m = FFT.get_m(dag_size)
        m_log2 = int(np.log2(m))
        tasks_count = int(m * m_log2 + 2 * m - 1)

        # generate tasks
        tasks: np.array(DAGSubTask) = []
        for task_id in range(tasks_count):
            task = DAGSubTask.generate(dag_id, task_id, task_type, memory_min, memory_max,
                                       execution_min, execution_max)
            tasks.append(task)

        # generate communication
        edges: list[list[int]] = []
        current_task_id = 1
        for i in range(1, 2 * m - 1):
            # binary section
            edges.append([(i - 1) // 2, i, 0])
            current_task_id += 1
        for i in range(m_log2):
            # butterfly section
            i_pow2 = int(np.power(2, i))
            is_right_direction: bool = True
            for j in range(m):
                edges.append([current_task_id - m, current_task_id, 0])
                if is_right_direction:
                    edges.append([current_task_id - m + i_pow2, current_task_id, 0])
                else:
                    edges.append([current_task_id - m - i_pow2, current_task_id, 0])
                if ((j + 1) % i_pow2) == 0:
                    is_right_direction = not is_right_direction

                current_task_id += 1

        # remove extra nodes to meet dag size
        tasks = tasks[:dag_size]
        edges = [edge for edge in edges if edge[0] < dag_size and edge[1] < dag_size]

        dag = DAG(DAGMode.FFT, dag_id, tasks, edges)
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
