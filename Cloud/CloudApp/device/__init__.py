import json
import os
import threading
import time
from enum import Enum

from ..algorithms.FuzzyScheduler import FuzzyScheduler
from ..algorithms.HEScheduler import HEScheduler
from ..algorithms.RandomScheduler import RandomScheduler
from ..algorithms.Scheduler import Scheduler
from ..dtos import FogSerializer
from ..dtos.EdgeSerializer import EdgeSerializer
from ..dtos.SubTaskSerializer import SubTaskSerializer
from ..types.Edge import Edge
from ..types.Fog import Fog
from ..types.PreemptionType import PreemptionType
from ..types.Processor import Processor
from ..types.SubTask import SubTask


class DeviceStatus(Enum):
    IDLE = 0,
    RUNNING = 1
    STOPPED = 2


class _Device:
    def __init__(self):
        self.status = DeviceStatus.IDLE
        self.start_time: float = 0
        self.time_scale: float = float(os.environ.get('TIME_SCALE', 1))
        self.total_time: int = int(os.environ.get('TOTAL_TIME', 10_000))
        self.preemption_type = PreemptionType[os.environ.get('PREEMPTION_TYPE', 'Lazy')]
        self.fogs: list[Fog] = []
        self.edges: list[Edge] = []
        self.algorithm: str = "MEES"
        self.output_name: str = ""

        # init processor characteristics
        processor_cores = int(os.environ.get('PROCESSOR_CORES', 4))
        processor_frequency = float(os.environ.get('PROCESSOR_FREQUENCY', 1.86))
        memory = int(os.environ.get('MEMORY', 4))
        active_power = float(os.environ.get('ACTIVE_POWER', 387))
        idle_power = float(os.environ.get('IDLE_POWER', 271))
        self.processors: list[Processor] = []
        for i in range(processor_cores):
            self.processors.append(Processor(i, processor_frequency, memory, active_power, idle_power))

        self.scheduler = None
        self.total_time_temp = self.total_time

    def start(self, algorithm: str, output_name: str):
        self.status = DeviceStatus.RUNNING
        self.algorithm = algorithm
        self.output_name = output_name
        self.start_time = time.time()

        if algorithm == "MEES":
            self.scheduler = Scheduler(self.processors, self.time_scale, self.preemption_type)
        elif algorithm == "HEFT_EDF":
            self.scheduler = HEScheduler(self.processors, self.time_scale, self.preemption_type)
        elif algorithm == "Random":
            self.scheduler = RandomScheduler(self.processors, self.time_scale, self.preemption_type)
        elif algorithm == "Fuzzy":
            self.scheduler = FuzzyScheduler(self.processors, self.time_scale, self.preemption_type)

        self.scheduler.start_time = self.start_time
        self.scheduler.clear()

        _thread = threading.Thread(target=self.run, args=())
        _thread.start()

    def register_fog(self, fog: FogSerializer):
        for i in range(len(self.fogs)):
            if self.fogs[i].address == fog['address']:
                self.fogs[i].coverage_area = fog['coverageArea']
                self.fogs[i].position_x = fog['positionX']
                self.fogs[i].position_y = fog['positionY']
                return
        self.fogs.append(Fog(fog))

    def register_edge(self, edge: EdgeSerializer):
        for i in range(len(self.edges)):
            if self.edges[i].address == edge['address']:
                return
        self.edges.append(Edge(edge))

    def get_nodes(self):
        return self.fogs, self.edges

    def add_task(self, edge_address: str, new_task: SubTaskSerializer):
        edge: Edge | None = None
        for i in range(len(self.edges)):
            if self.edges[i].address == edge_address:
                edge = self.edges[i]
                break
        if edge is None:
            raise Exception('Edge is not registered.')

        task = SubTask(edge, new_task['id'], new_task['workflowId'], new_task['jobId'], new_task['type'],
                       new_task['executionCost'],
                       new_task['memory'], new_task['absoluteDeadline'])
        self.scheduler.add_task(task)

    def run(self):
        # scheduling
        _scheduler_thread = threading.Thread(target=self.schedule, args=())
        _scheduler_thread.start()

    def schedule(self):
        max_scheduling_round_time = 0.0

        while DEVICE.status == DeviceStatus.RUNNING:

            f = time.time()

            current_time = int((time.time() - self.start_time) * 1000 * self.time_scale)
            self.scheduler.schedule(current_time, self.total_time)

            e = time.time()
            if e - f > max_scheduling_round_time:
                max_scheduling_round_time = e - f

            if current_time > self.total_time:
                DEVICE.status = DeviceStatus.STOPPED
                self.result()

        print("Max Scheduling Round Time: ", max_scheduling_round_time * 1000)

    def result(self):
        tasks_json = []
        for task in self.scheduler.tasks:
            tasks_json.append({
                'edge': task.edge.address,
                'index': task.index,
                'id': task.id,
                'workflowId': task.workflow_id,
                'jobId': task.job_id,
                'type': task.task_type.name,
                'executionCost': task.execution_cost,
                'memory': task.memory,
                'executionTimes': task.execution_times,
                'arrivalTime': task.arrival_time,
                'deadline': task.absolute_deadline,
            })

        with open(f'./Results/tasks-{self.algorithm}-{self.output_name}.json', "w") as file:
            file.write(json.dumps(tasks_json))

        processors_json = []
        for processor in self.processors:
            allocations_json = []
            for allocation in processor.allocations:
                task = self.scheduler.tasks[allocation[0]]
                allocations_json.append({
                    'index': task.index,
                    'startTime': allocation[1],
                    'endTime': allocation[2],
                    'taskId': task.id,
                    'workflowId': task.workflow_id,
                    'jobId': task.job_id,
                })

            processors_json.append({
                'frequency': processor.frequency,
                'activePower': processor.active_power,
                'idlePower': processor.idle_power,
                'memory': processor.memory,
                'allocations': allocations_json
            })

        with open(f'./Results/processors-{self.algorithm}-{self.output_name}.json', "w") as file:
            file.write(json.dumps(processors_json))

        for p in self.processors:
            print(f"Processing unit {p.index}:")
            total_active = 0
            for allocation in p.allocations:
                total_active += allocation[2] - allocation[1]
                task = self.scheduler.tasks[allocation[0]]
                print(
                    f"Task {task.id} | Job {task.job_id} | R {task.remaining_execution_cost} "
                    f"| DAG {task.workflow_id} | Executed at: {allocation[1]}-{allocation[2]}"
                    f" | D {task.absolute_deadline}")
            print(f"-----------------------------------------------------")
            energy = p.active_power * total_active + p.idle_power * (self.total_time - total_active)
            print(f"Energy {p.index}: {energy}")


DEVICE = _Device()
