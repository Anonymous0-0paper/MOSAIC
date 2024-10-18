import json
import os
import random
import threading
import time
from enum import Enum

from ..algorithms.FuzzyScheduler import FuzzyScheduler
from ..algorithms.HEScheduler import HEScheduler
from ..algorithms.RandomScheduler import RandomScheduler
from ..algorithms.Scheduler import Scheduler
from ..dtos.SubTaskSerializer import SubTaskSerializer
from ..types.Cloud import Cloud
from ..types.Edge import Edge
from ..types.PreemptionType import PreemptionType
from ..types.Processor import Processor
from ..types.SubTask import SubTask


class DeviceStatus(Enum):
    IDLE = 0,
    RUNNING = 1
    STOPPED = 2


class _Device:
    def __init__(self):
        self.cloud_address: str = os.environ.get('CLOUD_ADDRESS')
        self.address: str = os.environ.get('ADDRESS')

        self.status = DeviceStatus.IDLE
        self.start_time: float | None = None
        self.time_scale: float = float(os.environ.get('TIME_SCALE', 1))
        self.total_time: int = int(os.environ.get('TOTAL_TIME', 10_000))
        self.preemption_type = PreemptionType[os.environ.get('PREEMPTION_TYPE', 'Lazy')]
        self.algorithm: str = "MEES"
        self.output_name: str = ""

        # init device position characteristics
        position_x_max = int(os.environ.get('POSITION_X_MAX', 1000))
        position_y_max = int(os.environ.get('POSITION_Y_MAX', 1000))
        self.position_x = random.randint(0, position_x_max)
        self.position_y = random.randint(0, position_y_max)
        self.coverage_area = int(os.environ.get('COVERAGE_AREA', 100))

        # init processor characteristics
        processor_type = int(os.environ.get('PROCESSOR_TYPE', 0))
        if processor_type == 0:
            processor_cores = 18
            processor_frequency = 2.1
            memory = 8
            active_power = 557
            idle_power = 86.3
        elif processor_type == 1:
            processor_cores = 6
            processor_frequency = 3.06
            memory = 4
            active_power = 227
            idle_power = 62.2
        elif processor_type == 2:
            processor_cores = 8
            processor_frequency = 3.2
            memory = 8
            active_power = 62.5
            idle_power = 17.6
        else:
            processor_cores = 8
            processor_frequency = 3.2
            memory = 16
            active_power = 98.2
            idle_power = 22.6

        self.processors: list[Processor] = []
        for i in range(processor_cores):
            self.processors.append(Processor(i, processor_frequency, memory, active_power, idle_power))

        self.cloud = Cloud(self.cloud_address)
        self.cloud.register(self.address, self.position_x, self.position_y, self.coverage_area)
        self.scheduler = None

    def start(self, algorithm: str, output_name: str):
        self.status = DeviceStatus.RUNNING
        self.algorithm = algorithm
        self.output_name = output_name
        self.start_time = time.time()

        if algorithm == "MEES":
            self.scheduler = Scheduler(self.processors, self.time_scale, self.preemption_type, self.cloud)
        elif algorithm == "HEFT_EDF":
            self.scheduler = HEScheduler(self.processors, self.time_scale, self.preemption_type, self.cloud)
        elif algorithm == "Random":
            self.scheduler = RandomScheduler(self.processors, self.time_scale, self.preemption_type, self.cloud)
        elif algorithm == "Fuzzy":
            self.scheduler = FuzzyScheduler(self.processors, self.time_scale, self.preemption_type, self.cloud)

        self.scheduler.start_time = self.start_time
        self.scheduler.clear()

        _thread = threading.Thread(target=self.run, args=())
        _thread.start()

    def add_task(self, edge_address: str, new_task: SubTaskSerializer):
        edge = Edge(edge_address)

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
