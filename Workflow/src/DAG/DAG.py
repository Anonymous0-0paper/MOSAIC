import json
import math
from enum import Enum

import matplotlib.pyplot as plt
import networkx
from numpy import random

from Workflow.src.DAG.DAGSubTask import DAGSubTask, DAGSubTaskEncoder


class DAGMode(Enum):
    GE = "GE",
    FFT = "FFT",
    FullyTopology = "FullyTopology",
    Montage = "Montage",
    Genome1000 = "Genome1000",
    CasaWind = "CasaWind",



class DAG:

    def __init__(self, mode: DAGMode, id: int, subtasks: list[DAGSubTask], edges: list[list[int]]):
        self.mode = mode
        self.id = id
        self.subtasks = subtasks
        self.edges = edges  # [predecessor, successor, data size]
        self.deadline: int | None = None
        self.arrival_time: int | None = None

    def add_dummy_entry(self):
        entry_nodes = []
        for subtask in self.subtasks:
            if subtask.id not in [edge[1] for edge in self.edges]:
                entry_nodes.append(subtask.id)

        if len(entry_nodes) > 1:
            dummy_node = DAGSubTask(self.id, 0, self.subtasks[0].task_type)
            dummy_node.execution_cost = 0
            dummy_node.memory = 0

            # modify old ids
            for subtask in self.subtasks:
                subtask.id += 1
            for edge in self.edges:
                edge[0] += 1
                edge[1] += 1

            self.subtasks.insert(0, dummy_node)
            for entry in entry_nodes:
                self.edges.insert(0, [0, entry + 1, 0])

    def generate_deadline(self, deadline_min, deadline_max):
        self.deadline = random.randint(deadline_min, deadline_max)

    def generate_arrival_time(self, scale: float):
        self.arrival_time = int(random.uniform(0, 1) * scale)

    def generate_communication_data_sizes(self, communication_min: int, communication_max: int):
        for edge in self.edges:
            edge[2] = random.randint(communication_min, communication_max)

    def show(self, save: bool = False, file_path: str = "sample.svg"):
        g = networkx.DiGraph()
        g.add_nodes_from([subtask.id for subtask in self.subtasks])
        for edge in self.edges:
            g.add_edge(edge[0], edge[1])

        levels = []
        for i in range(len(self.subtasks)):
            level = 0
            for edge in self.edges:
                if edge[1] == i:
                    if level <= levels[edge[0]]:
                        level = levels[edge[0]] + 1
            levels.append(level)

        max_level = max(levels)
        levels_width = [0 for _ in range(max_level + 1)]
        for level in levels:
            levels_width[level] += 1

        max_width = max(levels_width)
        layout = networkx.spring_layout(g)
        x_array = [0 for _ in range(max_level + 1)]
        for i in range(len(self.subtasks)):
            level = levels[i]
            x: int | None = None
            if self.mode == DAGMode.FFT or self.mode == DAGMode.FullyTopology:
                x = int((x_array[level] - ((levels_width[level] - 1) / 2)) * (max_width / levels_width[level]) * 10)
            elif self.mode == DAGMode.GE:
                x = (x_array[level] + (level + 1) // 2) * 10
            else:
                x = int((x_array[level] - (levels_width[level] / 2)) * 10)

            layout[i] = (x, -10 * level)
            x_array[level] += 1

        node_attributes = {
            'node_color': 'lightblue',
            'node_size': 800,
            'font_size': 12,
            'font_color': 'black',
            'font_weight': 'bold',
        }
        edge_attributes = {
            'edge_color': 'gray',
            'width': 1.5,
            'arrows': True,
            'arrowstyle': '-|>',
            'arrowsize': 12,
        }
        plt.figure(figsize=(6, 6))
        networkx.draw_networkx(g, layout, with_labels=True, **node_attributes, **edge_attributes)

        if save:
            plt.savefig(file_path, format="svg")

        plt.show()

    @staticmethod
    def store(dags, file_path: str = "./Examples/dags.json"):

        dags_json = json.dumps(dags, indent=4, cls=DAGEncoder)

        with open(file_path, "w") as file:
            file.write(dags_json)


class DAGEncoder(json.JSONEncoder):

    def default(self, obj: DAG):
        if isinstance(obj, DAG):
            return {
                'id': obj.id,
                'mode': obj.mode.name,
                'subtasks': [DAGSubTaskEncoder().default(task) for task in obj.subtasks],
                'edges': obj.edges,
                'deadline': obj.deadline,
                'arrivalTime': obj.arrival_time
            }
        return super().default(obj)
