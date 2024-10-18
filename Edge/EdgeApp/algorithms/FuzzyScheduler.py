import math
import random
import time
from queue import Queue
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


class FuzzyScheduler:
    def __init__(self, processors: list[Processor], bus_bandwidth: int, time_scale: float,
                 preemption_type: PreemptionType, back_address: str, cloud: Cloud):
        self.processors = processors
        self.bus_bandwidth = bus_bandwidth
        self.start_time: float | None = None
        self.time_scale = time_scale
        self.dags: list[DAG] = []
        self.periodic_tasks: list[PeriodicTask] = []
        self.scheduling_queue = Queue()
        self.backup_queue = Queue()
        self.queue_lock = Lock()
        self.preemption_type: PreemptionType = preemption_type
        self.fogs: list[Fog] = []
        self.cloud: Cloud = cloud
        self.position: Tuple[int, int] | None = None
        self.back_address = back_address

    def clear(self):
        self.queue_lock.acquire()
        self.periodic_tasks.clear()
        self.dags.clear()
        for processor in self.processors:
            processor.clear()
        self.scheduling_queue.queue.clear()
        self.queue_lock.release()

    def add_dags(self, new_dags: list[DAG]):
        self.queue_lock.acquire()
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
                self.scheduling_queue.put((new_dags[i].arrival_time, j, i + dags_count, -1))
        self.queue_lock.release()

    def add_periodic_tasks(self, new_periodic_tasks: list[PeriodicTask]):
        self.queue_lock.acquire()
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

            self.scheduling_queue.put((arrival_time, index, -1, 0))
        self.queue_lock.release()

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
        self.queue_lock.acquire()
        q_size = self.scheduling_queue.qsize()
        for i in range(q_size):
            release_time, task_index, workflow_index, job_index = self.scheduling_queue.get()
            if current_time < release_time:
                self.backup_queue.put((release_time, task_index, workflow_index, job_index))
            elif current_time < self.data_availability(current_time, task_index, workflow_index):
                self.backup_queue.put((release_time, task_index, workflow_index, job_index))
            else:
                self.schedule_subtask(current_time, total_time, task_index, workflow_index, job_index)
        while not self.backup_queue.empty():
            self.scheduling_queue.put(self.backup_queue.get())

        self.queue_lock.release()

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

    def schedule_subtask(self, start_time: int,  total_time: int, task_index: int, workflow_index: int, job_index: int):
        candidate_processor: Processor | None = None
        task: SubTask = self.periodic_tasks[task_index] if workflow_index == -1 \
            else self.dags[workflow_index].subtasks[task_index]

        for p in self.processors:
            idle = self.check_processor(p, start_time, task_index, workflow_index, job_index, True)
            if idle:
                candidate_processor = p
                break

        fuzzy_value = self.fuzzy_offload_decision(task, candidate_processor, start_time)

        if task.task_type != TaskType.HARD and fuzzy_value > 0.5 and task.execution_cost != 0:
            self.offload(task)
        else:
            if candidate_processor is None:
                self.backup_queue.put((task.arrival_time, task_index, workflow_index, job_index))
                return

            new_idle = self.check_processor(candidate_processor, start_time, task_index, workflow_index, job_index,
                                            False)
            if not new_idle:
                print("Warn")

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
            self.scheduling_queue.put((job.arrival_time, job.index, -1, job.job_index))

    def check_processor(self, p: Processor, start_time: int, task_index: int, workflow_index: int, job_index: int,
                        only_check: bool) -> bool:

        task: SubTask = self.periodic_tasks[task_index] if workflow_index == -1 \
            else self.dags[workflow_index].subtasks[task_index]

        execution_time = p.get_execution_time(task.remaining_execution_cost)

        if len(p.allocations) > 0:
            if p.allocations[-1][4] > start_time:
                return False

        end_time = start_time + execution_time

        if not only_check:
            task.remaining_execution_cost = 0
            task.execution_times = [[p.index, start_time, end_time]]
            p.allocations.append([task_index, workflow_index, job_index, start_time, end_time])

        return True

    def offload(self, task: SubTask):
        available_fogs_index = []
        for i in range(len(self.fogs)):
            fog = self.fogs[i]
            if fog.is_in_range(self.position[0], self.position[1]):
                available_fogs_index.append(i)

        if len(available_fogs_index) != 0:
            # select randomly one fog or cloud
            selected_fog_index = random.choice(available_fogs_index)
            self.fogs[selected_fog_index].offload(self.back_address, task)
            task.offload_time = time.time()

        if len(available_fogs_index) == 0 and self.cloud is not None:
            # offload on cloud
            self.cloud.offload(self.back_address, task)
            task.offload_time = time.time()

    def update_network(self):
        self.fogs = self.cloud.get_nodes()

    def fuzzy_offload_decision(self, task: SubTask, processor: Processor | None, current_time):
        """
        Fuzzy-based decision making for offloading a task.
        This function calculates fuzzy membership values based on deadline, and EFT.
        """
        deadline_fuzzy = self.fuzzy_deadline(task.deadline, task.arrival_time, current_time)
        eft_fuzzy = self.fuzzy_eft(processor, task.deadline, task.arrival_time, current_time, task.execution_cost)
        offload_fuzzy_value = (deadline_fuzzy * 0.5) + (eft_fuzzy * 0.5)
        return offload_fuzzy_value

    def fuzzy_deadline(self, deadline: int, arrival_time: int, current_time: int):
        remaining_time = deadline + arrival_time - current_time
        if remaining_time < deadline * 0.5:  # tight deadline
            return 1.0
        elif remaining_time < deadline * 0.7:
            return 0.7
        else:
            return 0.4

    def fuzzy_eft(self, processor: Processor | None, deadline: int, arrival_time: int,
                  current_time: int, execution_cost: int):
        if processor is None:
            return 0.7
        execution_time = processor.get_execution_time(execution_cost)

        eft = current_time + execution_time

        if eft > deadline + arrival_time:  # EFT exceeds deadline
            return 1.0
        elif eft > deadline * 0.7 + arrival_time:
            return 0.7
        else:
            return 0.4
