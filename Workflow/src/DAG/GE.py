import math

import numpy as np

from Workflow.src.DAG.DAG import DAG, DAGMode
from Workflow.src.DAG.DAGSubTask import DAGSubTask
from Workflow.src.SubTask import TaskType


class GE:

    @staticmethod
    def generate_dag(dag_id: int, dag_size: int, task_type: TaskType, arrival_scale: float,
                     memory_min: int, memory_max: int, execution_min: int, execution_max: int,
                     deadline_min: int, deadline_max: int, communication_min: int, communication_max: int) -> DAG:
        m = GE.get_m(dag_size)
        tasks_count = int((m ** 2 + m - 2) / 2)

        # generate tasks
        tasks: np.array(DAGSubTask) = []
        for task_id in range(tasks_count):
            task = DAGSubTask.generate(dag_id, task_id, task_type, memory_min, memory_max,
                                       execution_min, execution_max)
            tasks.append(task)

        # generate communication
        edges: list[list[int]] = []
        current_task_id = 0
        for new_tasks in range(m, 1, -1):
            for successor_id in range(current_task_id + 1, current_task_id + new_tasks):
                edges.append([current_task_id, successor_id, 0])
                if new_tasks != 2:
                    edges.append([successor_id, successor_id + new_tasks - 1, 0])

            current_task_id += new_tasks

        # remove extra nodes to meet dag size
        tasks = tasks[:dag_size]
        edges = [edge for edge in edges if edge[0] < dag_size and edge[1] < dag_size]

        dag = DAG(DAGMode.GE, dag_id, tasks, edges)
        dag.generate_deadline(deadline_min, deadline_max)
        dag.generate_arrival_time(arrival_scale)
        dag.generate_communication_data_sizes(communication_min, communication_max)
        return dag

    @staticmethod
    def get_m(dag_size: int) -> int:
        return int(math.ceil((math.sqrt(9 + 8 * dag_size) - 1) / 2))
