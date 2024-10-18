import json
import os
import random
import threading
import time
from enum import Enum

from .mobility import random_walk, levy_walk, WalkMode
from ..algorithms.FuzzyScheduler import FuzzyScheduler
from ..algorithms.HEScheduler import HEScheduler
from ..algorithms.RandomScheduler import RandomScheduler
from ..algorithms.Scheduler import Scheduler
from ..dtos import PeriodicTaskSerializer
from ..dtos.DagSerializer import DagSerializer
from ..types.Cloud import Cloud
from ..types.DAG import DAG
from ..types.PeriodicTask import PeriodicTask
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
        self.back_address = os.environ.get('ADDRESS')

        self.positions: list[tuple[int | None, int | None]] = []
        self.walk_model: str | None = None
        self.status = DeviceStatus.IDLE
        self.start_time: float = 0
        self.time_scale: float = float(os.environ.get('TIME_SCALE', 1))
        self.total_time: int = int(os.environ.get('TOTAL_TIME', 100_000))
        self.scheduler_total_time: int = int(os.environ.get('SCHEDULER_TOTAL_TIME', 50_000))
        self.walk_model: str = os.environ.get('WALK_MODE', WalkMode.Random)
        self.speed: float = float(os.environ.get('SPEED', 1.0))
        self.preemption_type = PreemptionType[os.environ.get('PREEMPTION_TYPE', 'Lazy')]
        self.algorithm: str = "MEES"
        self.output_name: str = ""

        # init device position characteristics
        position_x_max = int(os.environ.get('POSITION_X_MAX', 1000))
        position_y_max = int(os.environ.get('POSITION_Y_MAX', 1000))
        start_position_x = random.randint(0, position_x_max)
        start_position_y = random.randint(0, position_y_max)
        self.max_position = (position_x_max, position_y_max)
        self.start_position = (start_position_x, start_position_y)
        self.positions = [(start_position_x, start_position_y)]

        # init processor characteristics
        self.bus_bandwidth = int(os.environ.get('BUS_BANDWIDTH', 100))

        processor_type = int(os.environ.get('PROCESSOR_TYPE', 0))
        if processor_type == 0 or processor_type == 1:
            processor_cores = 4
            processor_frequency = 1.5
            memory = 2 if processor_type == 0 else 4
            active_power = 8
            idle_power = 2.7
        elif processor_type == 2:
            processor_cores = 4
            processor_frequency = 1.4
            memory = 1
            active_power = 4.5
            idle_power = 2
        elif processor_type == 3:
            processor_cores = 4
            processor_frequency = 2.83
            memory = 4
            active_power = 118
            idle_power = 56.7
        elif processor_type == 4:
            processor_cores = 4
            processor_frequency = 2.83
            memory = 2
            active_power = 95.4
            idle_power = 49.6
        else:
            processor_cores = 4
            processor_frequency = 2.4
            memory = 2 if processor_type == 5 else 4
            active_power = 9
            idle_power = 2.75

        self.processors: list[Processor] = []
        for i in range(processor_cores):
            self.processors.append(Processor(i, processor_frequency, memory, active_power, idle_power))

        # init scheduling algorithm
        self.cloud = Cloud(self.cloud_address)
        self.cloud.register(self.back_address)
        self.scheduler = None

    def start(self, algorithm: str, output_name: str):
        self.status = DeviceStatus.RUNNING
        self.algorithm = algorithm
        self.output_name = output_name
        self.start_time = time.time()

        if algorithm == "MEES":
            self.scheduler = Scheduler(self.processors, self.bus_bandwidth, self.time_scale,
                                       self.preemption_type, self.back_address, self.cloud)
        elif algorithm == "HEFT_EDF":
            self.scheduler = HEScheduler(self.processors, self.bus_bandwidth, self.time_scale,
                                         self.preemption_type, self.back_address, self.cloud)
        elif algorithm == "Random":
            self.scheduler = RandomScheduler(self.processors, self.bus_bandwidth, self.time_scale,
                                             self.preemption_type, self.back_address, self.cloud)
        elif algorithm == "Fuzzy":
            self.scheduler = FuzzyScheduler(self.processors, self.bus_bandwidth, self.time_scale,
                                            self.preemption_type, self.back_address, self.cloud)

        self.scheduler.start_time = self.start_time
        self.scheduler.clear()
        self.positions = [self.start_position]

        _thread = threading.Thread(target=self.run, args=())
        _thread.start()

    def add_dags(self, new_dags: list[DagSerializer]):
        dags: list[DAG] = []
        for i in range(len(new_dags)):
            dag = DAG(new_dags[i])
            dags.append(dag)
        self.scheduler.add_dags(dags)
        if self.status != DeviceStatus.RUNNING:
            self.status = DeviceStatus.RUNNING
            _thread = threading.Thread(target=self.run, args=())
            _thread.start()

    def add_periodic_tasks(self, new_periodic_tasks: list[PeriodicTaskSerializer]):
        periodic_tasks: list[PeriodicTask] = []
        for i in range(len(new_periodic_tasks)):
            dto = new_periodic_tasks[i]
            periodic_task = PeriodicTask(dto['id'], 0, dto['type'], dto['executionCost'], dto['memory'],
                                         dto['deadline'])
            periodic_tasks.append(periodic_task)
        self.scheduler.add_periodic_tasks(periodic_tasks)

    def get_last_positions(self, max_count: int) -> list[tuple[int | None, int | None]]:
        if max_count > len(self.positions):
            if len(self.positions) > 0:
                return self.positions
            else:
                return [(None, None)]

        return self.positions[len(self.positions) - max_count:]

    def notify_execute_task(self, task_id: int, workflow_id: int, job_id: int):
        current_time = int((time.time() - self.start_time) * 1000 * self.time_scale)
        self.scheduler.notify_execute_task(current_time, task_id, workflow_id, job_id)

    def run(self):
        # Simulation of the device's walking steps
        _walk_thread = threading.Thread(target=self.walk, args=())
        _walk_thread.start()

        # scheduling
        _scheduler_thread = threading.Thread(target=self.schedule, args=())
        _scheduler_thread.start()

    def walk(self):
        total_stored_steps = 100
        remaining_steps: float = 0

        while DEVICE.status == DeviceStatus.RUNNING:
            remaining_steps += self.speed
            if remaining_steps > 1:
                steps = int(remaining_steps)
                remaining_steps = remaining_steps - steps
                if self.walk_model == "Random":
                    self.positions.append(random_walk(steps, self.positions[-1], self.max_position))
                else:
                    self.positions.append(levy_walk(steps, self.positions[-1], self.max_position))
            if len(self.positions) > total_stored_steps:
                del self.positions[:total_stored_steps // 2]

            time.sleep(1 / (1000 * self.time_scale))

    def schedule(self):
        self.scheduler.update_network()

        while DEVICE.status == DeviceStatus.RUNNING:
            current_time = int((time.time() - self.start_time) * 1000 * self.time_scale)
            self.scheduler.update_position((self.positions[-1][0], self.positions[-1][1]))
            self.scheduler.schedule(current_time, self.scheduler_total_time)

            if current_time > self.total_time:
                DEVICE.status = DeviceStatus.STOPPED
                self.result()

    def result(self):
        tasks_json = []
        for dag in self.scheduler.dags:
            for task in dag.subtasks:
                tasks_json.append({
                    'id': task.id,
                    'workflowId': task.workflow_id,
                    'jobId': task.job_id,
                    'type': task.task_type.name,
                    'executionCost': task.execution_cost,
                    'memory': task.memory,
                    'executionTimes': task.execution_times,
                    'arrivalTime': task.arrival_time,
                    'deadline': task.deadline,
                    'latency': task.latency,
                    'offloadTime': int((task.offload_time - self.start_time) * 1000 * self.time_scale) if (
                            task.offload_time is not None) else None,
                    'remainingExecutionCost': task.remaining_execution_cost,
                })
        for task in self.scheduler.periodic_tasks:
            tasks_json.append({
                'id': task.id,
                'workflowId': task.workflow_id,
                'jobId': task.job_id,
                'type': task.task_type.name,
                'executionCost': task.execution_cost,
                'memory': task.memory,
                'executionTimes': task.execution_times,
                'arrivalTime': task.arrival_time,
                'deadline': task.deadline,
                'latency': task.latency,
                'offloadTime': int((task.offload_time - self.start_time) * 1000 * self.time_scale) if (
                        task.offload_time is not None) else None,
                'remainingExecutionCost': task.remaining_execution_cost,
            })

        with open(f'./Results/tasks-{self.algorithm}-{self.output_name}.json', "w") as file:
            file.write(json.dumps(tasks_json))

        processors_json = []
        for processor in self.processors:
            allocations_json = []
            for allocation in processor.allocations:
                task = self.scheduler.periodic_tasks[allocation[0]] if allocation[1] == -1 else \
                    self.scheduler.dags[allocation[1]].subtasks[allocation[0]]
                allocations_json.append({
                    'startTime': allocation[3],
                    'endTime': allocation[4],
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
                total_active += allocation[4] - allocation[3]
                dag_id = -1 if allocation[1] == -1 else self.scheduler.dags[allocation[1]].id
                task = self.scheduler.periodic_tasks[allocation[0]] if allocation[1] == -1 else \
                    self.scheduler.dags[allocation[1]].subtasks[allocation[0]]
                print(
                    f"Task {task.id} | Job {allocation[2]} | R {task.remaining_execution_cost} "
                    f"| DAG {dag_id} | Executed at: {allocation[3]}-{allocation[4]} | D {task.deadline}")
            print(f"-----------------------------------------------------")
            energy = p.active_power * total_active + p.idle_power * (self.total_time - total_active)
            print(f"Energy {p.index}: {energy}")

    def qos(self, task: SubTask) -> float:
        if task.execution_cost == 0:
            return 1  # dummy task

        # offloaded task
        if len(task.execution_times) == 1:
            if task.execution_times[0][0] == -1:
                if task.execution_times[0][2] >= task.deadline + task.arrival_time:
                    return 1
                return 0

        # other tasks
        ex_before_deadline = 0
        ex_after_deadline = task.remaining_execution_cost

        for ex in task.execution_times:
            if ex[2] <= task.deadline + task.arrival_time:
                ex_before_deadline += self.processors[ex[0]].get_execution_cost(ex[2] - ex[1])
            elif ex[1] < task.deadline + task.arrival_time < ex[2]:
                ex_before_deadline += self.processors[ex[0]].get_execution_cost(task.deadline
                                                                                + task.arrival_time - ex[1])
                ex_after_deadline += self.processors[ex[0]].get_execution_cost(ex[2] -
                                                                               task.deadline + task.arrival_time)
            else:
                ex_after_deadline += self.processors[ex[0]].get_execution_cost(ex[2] - ex[1])

        return ex_before_deadline / (ex_after_deadline + ex_before_deadline)


DEVICE = _Device()
