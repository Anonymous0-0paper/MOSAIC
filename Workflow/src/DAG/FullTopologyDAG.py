import random
from itertools import permutations

import numpy as np

from Workflow.src.DAG.DAG import DAG, DAGMode
from Workflow.src.DAG.DAGSubTask import DAGSubTask
from Workflow.src.SubTask import TaskType

all_communications: list[np.array(np.array(bool))] = []
all_tasks_labels: list[np.array(int)] = []


class FullTopologyDAG:

    @staticmethod
    def generate_dag(dag_id: int, dag_size: int, task_type: TaskType, arrival_scale: float,
                     memory_min: int, memory_max: int, execution_min: int, execution_max: int,
                     deadline_min: int, deadline_max: int, communication_min: int, communication_max: int,
                     deg_in_max: int, deg_out_max: int, l_min: int,
                     l_max: int, sh_min: int, sh_max: int, seed: list) -> DAG:

        comb = FullTopologyDAG.comb(dag_size, l_min, l_max, sh_min, sh_max)
        selected_comb: list[int]
        if seed[0] != -1:
            selected_comb = comb[seed[0]]
        else:
            selected_comb = random.choice(comb)

        perm = FullTopologyDAG.perm(deg_out_max, selected_comb)
        selected_perm: list[int]
        if seed[1] != -1:
            selected_perm = perm[seed[1]]
        else:
            selected_perm = random.choice(perm)

        if seed[2] != -1:
            FullTopologyDAG.conn(deg_in_max, deg_out_max, selected_perm)
            communications: np.array(np.array(bool)) = all_communications[seed[2]]
            print("Available seeds: ", len(comb), len(perm), len(all_communications))
        else:
            FullTopologyDAG.random_conn(deg_in_max, deg_out_max, selected_perm)
            communications: np.array(np.array(bool)) = random.choice(all_communications)

            print(len(perm), selected_perm)
        # generate tasks
        tasks_count = sum(selected_perm)
        tasks: np.array(DAGSubTask) = []
        for task_id in range(tasks_count):
            task = DAGSubTask.generate(dag_id, task_id, task_type, memory_min, memory_max,
                                       execution_min, execution_max)
            tasks.append(task)

        edges: list[list[int]] = []
        for i in range(tasks_count):
            for j in range(i, tasks_count):
                if communications[i][j]:
                    edges.append([i, j, 0])
        dag = DAG(DAGMode.FullyTopology, dag_id, tasks, edges)
        dag.generate_deadline(deadline_min, deadline_max)
        dag.generate_arrival_time(arrival_scale)
        dag.generate_communication_data_sizes(communication_min, communication_max)
        dag.add_dummy_entry()
        return dag

    @staticmethod
    def comb(n: int, l_min: int, l_max: int, sh_min: int, sh_max: int) -> list[list[int]]:
        c_shape: list[list[int]] = []
        if l_min == 1:
            if n <= sh_max:
                c_shape.append([n])

        if l_max > 1:
            for x_i in range(sh_min, min(n - 1, sh_max) + 1):
                new_n = n - x_i
                new_shapes = FullTopologyDAG.comb(new_n, max(1, l_min - 1), l_max - 1, 1, x_i)
                for shape in new_shapes:
                    shape.insert(0, x_i)
                    c_shape.append(shape)
                pass

        return c_shape

    @staticmethod
    def perm(deg_out_max: int, shape: list[int]) -> list[list[int]]:
        sp_shape: list[list[int]] = []

        for perm in set(permutations(shape)):
            valid_perm = True
            for i in range(1, len(perm)):
                if perm[i] > perm[i - 1] * deg_out_max:
                    valid_perm = False
                    break
            if valid_perm:
                sp_shape.append(list(perm))

        return sp_shape

    @staticmethod
    def conn(deg_in_max: int, deg_out_max: int, shape: list[int]):
        nodes_by_level: list[list[int]] = []
        tasks_count = 0
        for l in shape:
            nodes_by_level.append([task_id for task_id in range(tasks_count, tasks_count + l)])
            tasks_count += l

        nodes_free_degree: list[int] = [deg_out_max for _ in range(tasks_count)]
        communications: np.array(np.array(bool)) = np.zeros((tasks_count, tasks_count), dtype=bool)
        tasks_labels = [0] * tasks_count

        FullTopologyDAG.conn_recursive(nodes_by_level, nodes_free_degree, communications, tasks_labels,
                                       deg_in_max, deg_out_max, 1, nodes_by_level[1][0], -1, -1)

    @staticmethod
    def conn_recursive(nodes_by_level: list[list[int]], nodes_free_degree: list[int],
                       communications: np.array(np.array(bool)), tasks_labels: list[int],
                       deg_in_max: int, deg_out_max: int, current_level: int, current_node: int,
                       remaining_degree: int, recent_prev_node: int):

        def make_connection():
            connect_labels: list[int] = []
            for prev_node in nodes_by_level[current_level - 1]:
                if (nodes_free_degree[prev_node] == 0 or communications[prev_node, current_node]
                        or recent_prev_node >= prev_node):
                    continue

                if tasks_labels[prev_node] in connect_labels:
                    continue

                communications[prev_node, current_node] = True
                nodes_free_degree[prev_node] -= 1
                connect_labels.append(tasks_labels[prev_node])
                FullTopologyDAG.conn_recursive(nodes_by_level, nodes_free_degree, communications, tasks_labels,
                                               deg_in_max, deg_out_max, current_level, current_node,
                                               remaining_degree - 1, prev_node)
                # rollback changes
                communications[prev_node, current_node] = False
                nodes_free_degree[prev_node] += 1

        def assign_tasks_labels():
            last_label = max(tasks_labels[:nodes_by_level[current_level][0]])
            label_group: list[list[bool]] = []
            for node in nodes_by_level[current_level]:
                find_group = False
                for g in range(len(label_group)):
                    same_group = True
                    for j in range(0, node):
                        if communications[j, node] != label_group[g][j]:
                            same_group = False
                            break
                    if same_group:
                        tasks_labels[node] = last_label + g + 1
                        find_group = True
                        break
                if not find_group:
                    label_group.append(communications[:, node])
                    tasks_labels[node] = last_label + len(label_group)

        if remaining_degree == 0:
            current_node += 1
            if nodes_by_level[current_level][-1] < current_node:
                assign_tasks_labels()
                current_level += 1
            if current_level == len(nodes_by_level):
                all_communications.append(np.copy(communications))
                all_tasks_labels.append(np.copy(tasks_labels))
            else:
                FullTopologyDAG.conn_recursive(nodes_by_level, nodes_free_degree, communications, tasks_labels,
                                               deg_in_max, deg_out_max, current_level, current_node,
                                               -1, -1)

        elif remaining_degree == -1:
            for deg_in in range(1, deg_in_max + 1):
                FullTopologyDAG.conn_recursive(nodes_by_level, nodes_free_degree, communications, tasks_labels,
                                               deg_in_max, deg_out_max, current_level, current_node,
                                               deg_in, -1)

        else:
            make_connection()

    @staticmethod
    def random_conn(deg_in_max: int, deg_out_max: int, shape: list[int]):
        nodes_by_level: list[list[int]] = []
        tasks_count = 0
        for l in shape:
            nodes_by_level.append([task_id for task_id in range(tasks_count, tasks_count + l)])
            tasks_count += l

        nodes_free_degree: list[int] = [deg_out_max for _ in range(tasks_count)]
        communications: np.array(np.array(bool)) = np.zeros((tasks_count, tasks_count), dtype=bool)

        current_node = nodes_by_level[1][0]
        current_level = 1
        deg_in: int = np.random.randint(1, deg_in_max + 1)
        while current_node != tasks_count:
            available_predecessors: list[int] = []
            for predecessor in nodes_by_level[current_level - 1]:
                if nodes_free_degree[predecessor] > 0:
                    available_predecessors.append(predecessor)
            if len(available_predecessors) == 0:
                print("Error generating Fully Topology DAG, Try again...")
                return FullTopologyDAG.random_conn(deg_in_max, deg_out_max, shape)
            predecessors: list[int] = np.random.choice(available_predecessors, deg_in)
            for predecessor in predecessors:
                communications[predecessor, current_node] = True
                nodes_free_degree[predecessor] -= 1
            current_node += 1
            if nodes_by_level[current_level][-1] < current_node:
                current_level += 1
                deg_in: int = np.random.randint(1, deg_in_max + 1)

        all_communications.append(communications)
