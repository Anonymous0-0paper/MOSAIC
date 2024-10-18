import math
import random
import time
from threading import Lock
from typing import Tuple

from .HEFT import HEFT
from ..types.Cloud import Cloud
from ..types.DAG import DAG
from ..types.Fog import Fog
from ..types.PeriodicTask import PeriodicTask
from ..types.PreemptionType import PreemptionType
from ..types.Processor import Processor
from ..types.SubTask import SubTask, TaskType


class RandomScheduler:
    def __init__(self, processors: list[Processor], bus_bandwidth: int, time_scale: float,
                 preemption_type: PreemptionType, back_address: str, cloud: Cloud):
        self.processors = processors
        self.bus_bandwidth = bus_bandwidth
        self.start_time: float | None = None
        self.time_scale = time_scale
        self.dags: list[DAG] = []
        self.periodic_tasks: list[PeriodicTask] = []
        self.preemption_type: PreemptionType = preemption_type
        self.fogs: list[Fog] = []
        self.cloud: Cloud = cloud
        self.position: Tuple[int, int] | None = None
        self.back_address = back_address

        self.ready_tasks: list[Tuple[int, int, int]] = []
        self.ready_tasks_lock = Lock()

    def clear(self):
        self.ready_tasks_lock.acquire()
        self.periodic_tasks.clear()
        self.dags.clear()
        for processor in self.processors:
            processor.clear()
        self.ready_tasks.clear()
        self.ready_tasks_lock.release()

    def add_dags(self, new_dags: list[DAG]):
        self.ready_tasks_lock.acquire()
        dags_count = len(self.dags)
        for i in range(len(new_dags)):
            heft = HEFT(new_dags[i], self.processors, self.bus_bandwidth)
            heft.schedule()
            heft.assign_subtask_deadlines()
            self.dags.append(new_dags[i])
            for j in range(len(new_dags[i].subtasks)):
                new_dags[i].subtasks[j].index = j
                new_dags[i].subtasks[j].arrival_time = new_dags[i].arrival_time
                new_dags[i].subtasks[j].absolute_deadline = (float(new_dags[i].subtasks[j].deadline)
                                                             + new_dags[i].arrival_time) / 1000 + self.start_time
                self.ready_tasks.append((j, dags_count + i, -1))
        self.ready_tasks_lock.release()

    def add_periodic_tasks(self, new_periodic_tasks: list[PeriodicTask]):
        self.ready_tasks_lock.acquire()
        arrival_time = int((time.time() - self.start_time) * 1000 * self.time_scale)
        periodic_tasks_count = len(self.periodic_tasks)
        self.periodic_tasks.extend(new_periodic_tasks)
        for i in range(len(new_periodic_tasks)):
            index = i + periodic_tasks_count
            new_periodic_tasks[i].index = index
            new_periodic_tasks[i].arrival_time = arrival_time
            new_periodic_tasks[i].absolute_deadline = ((float(new_periodic_tasks[i].deadline)
                                                        + new_periodic_tasks[i].arrival_time) / 1000
                                                       + self.start_time)

            self.ready_tasks.append((index, -1, 0))
        self.ready_tasks_lock.release()

    def update_position(self, position: Tuple[int, int]):
        self.position = position

    def notify_execute_task(self, current_time: int, task_id: int, workflow_id: int, job_id: int):
        if workflow_id == -1:
            for task in self.periodic_tasks:
                if task.id == task_id and task.job_id == job_id:
                    task.remaining_execution_cost = 0
                    task.execution_times = [[-1, current_time, current_time]]
                    task.latency = (time.time() - task.offload_time) * 1000
                    break
        else:
            for dag in self.dags:
                if dag.id == workflow_id:
                    for task in dag.subtasks:
                        if task.id == task_id:
                            task.remaining_execution_cost = 0
                            task.execution_times = [[-1, current_time, current_time]]
                            task.latency = (time.time() - task.offload_time) * 1000
                            break
                    break

    def schedule(self, current_time: int, total_time: int):
        self.ready_tasks_lock.acquire()

        max_checked = 100
        checked = 0
        while True:
            if len(self.ready_tasks) == 0 or checked == max_checked:
                break

            selected_index = random.randint(0, len(self.ready_tasks) - 1)
            selected_ready_task = self.ready_tasks[selected_index]
            selected_task: SubTask = self.periodic_tasks[selected_ready_task[0]] \
                if selected_ready_task[1] == -1 \
                else self.dags[selected_ready_task[1]].subtasks[selected_ready_task[0]]

            if current_time < selected_task.arrival_time:
                checked += 1
                continue
            if current_time < self.data_availability(current_time, selected_ready_task[0], selected_ready_task[1]):
                checked += 1
                continue

            self.schedule_subtask(current_time, total_time, selected_ready_task[0], selected_ready_task[1],
                                  selected_ready_task[2])
            del self.ready_tasks[selected_index]

        self.ready_tasks_lock.release()

    def data_availability(self, current_time: int, task_index: int, workflow_index: int) -> int:
        if workflow_index == -1:
            return 0

        data_available = 0
        predecessors = [(edge[0], edge[2]) for edge
                        in self.dags[workflow_index].edges
                        if edge[1] == task_index]

        for predecessor in predecessors:
            task = self.dags[workflow_index].subtasks[predecessor[0]]
            if task.remaining_execution_cost != 0:
                return current_time + 1

            if task.execution_cost == 0:
                # dummy task
                continue

            data_available_temp = task.execution_times[-1][2]
            if data_available < data_available_temp:
                data_available = data_available_temp

        return data_available

    def schedule_subtask(self, start_time: int, total_time: int, task_index: int, workflow_index: int, job_index: int):
        task: SubTask = self.periodic_tasks[task_index] if workflow_index == -1 \
            else self.dags[workflow_index].subtasks[task_index]

        if task.task_type != TaskType.HARD and random.uniform(0, 1) < 0.8 and task.execution_cost != 0:
            self.offload(task)
        else:
            processor_index = random.randint(0, len(self.processors) - 1)
            if len(self.processors[processor_index].allocations) > 0:
                start_time = max(start_time, self.processors[processor_index].allocations[-1][4])

            end_time = start_time + self.processors[processor_index].get_execution_time(task.execution_cost)

            task.remaining_execution_cost = 0
            task.execution_times = [[processor_index, start_time, end_time]]
            self.processors[processor_index].allocations.append([
                task_index, workflow_index, job_index, start_time, end_time])

        if workflow_index == -1:
            for i in range(task_index + 1, len(self.periodic_tasks)):
                if self.periodic_tasks[i].id == self.periodic_tasks[task_index].id:
                    return
            current_job = self.periodic_tasks[task_index]
            job = PeriodicTask(current_job.id, current_job.job_index + 1, current_job.task_type.name,
                               current_job.execution_cost, current_job.memory, current_job.deadline)
            job.index = len(self.periodic_tasks)
            job.arrival_time = current_job.arrival_time + current_job.period
            job.absolute_deadline = ((float(job.deadline) + job.arrival_time) / 1000
                                     + self.start_time)

            if job.deadline + job.arrival_time >= total_time:
                return
            self.periodic_tasks.append(job)
            self.ready_tasks.append((job.index, -1, job.job_index))

    def offload(self, task: SubTask):
        available_fogs_index = []
        for i in range(len(self.fogs)):
            fog = self.fogs[i]
            if fog.is_in_range(self.position[0], self.position[1]):
                available_fogs_index.append(i)

        if len(available_fogs_index) != 0 and random.uniform(0, 1) < 0.5:
            # select randomly one fog
            selected_fog_index = random.choice(available_fogs_index)
            self.fogs[selected_fog_index].offload(self.back_address, task)
            task.offload_time = time.time()

        else:
            # offload on cloud
            self.cloud.offload(self.back_address, task)
            task.offload_time = time.time()

    def update_network(self):
        self.fogs = self.cloud.get_nodes()
