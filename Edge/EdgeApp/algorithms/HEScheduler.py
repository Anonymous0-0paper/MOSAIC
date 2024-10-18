import math
import random
import time
from queue import Queue
from threading import Lock
from typing import Tuple

from .HEFT import HEFT
from .SchedulerPriorityQueue import SchedulerPriority
from ..types.Cloud import Cloud
from ..types.DAG import DAG
from ..types.Fog import Fog
from ..types.PeriodicTask import PeriodicTask
from ..types.PreemptionType import PreemptionType
from ..types.Processor import Processor
from ..types.SubTask import SubTask, TaskType


class HEScheduler:
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
                self.scheduling_queue.put((new_dags[i].subtasks[j].deadline + new_dags[i].arrival_time,
                                           new_dags[i].arrival_time, j, i + dags_count, -1))
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

            self.scheduling_queue.put((new_periodic_tasks[i].deadline + arrival_time,
                                       arrival_time, index, -1, 0))
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
            deadline, release_time, task_index, workflow_index, job_index = self.scheduling_queue.get()
            if current_time < release_time:
                self.backup_queue.put((deadline, release_time, task_index, workflow_index, job_index))
            elif current_time < self.data_availability(current_time, task_index, workflow_index):
                self.backup_queue.put((deadline, release_time, task_index, workflow_index, job_index))
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

    def schedule_subtask(self, start_time: int, total_time: int, task_index: int, workflow_index: int, job_index: int):
        eft = math.inf
        eft_processor: Processor | None = None
        task: SubTask = self.periodic_tasks[task_index] if workflow_index == -1 \
            else self.dags[workflow_index].subtasks[task_index]

        for p in self.processors:
            if workflow_index == -1 and p.index % 2 == 0:
                continue
            if workflow_index != -1 and p.index % 2 == 1:
                continue
            eft_candidate = self.eft(p, start_time, task_index, workflow_index, job_index, True)
            if eft_candidate < eft:
                eft = eft_candidate
                eft_processor = p

        if task.task_type != TaskType.HARD and random.uniform(0, 1) < 0.8 and len(
                task.execution_times) == 0 and task.execution_cost != 0:
            self.offload(task)
        else:
            new_eft = self.eft(eft_processor, start_time, task_index, workflow_index, job_index, False)
            if eft != new_eft:
                print("Warning: Code 24")

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
            self.scheduling_queue.put((job.deadline + job.arrival_time,
                                       job.arrival_time, job.index, -1, job.job_index))

    def eft(self, p: Processor, start_time: int, task_index: int, workflow_index: int, job_index: int,
            only_check: bool) -> int:

        task: SubTask = self.periodic_tasks[task_index] if workflow_index == -1 \
            else self.dags[workflow_index].subtasks[task_index]

        execution_time = p.get_execution_time(task.remaining_execution_cost)
        start_time_temp = start_time
        if len(task.execution_times) > 0:
            start_time_temp = max(start_time_temp, task.execution_times[-1][2])
        index = -1
        i = 0
        prev_scheduled_task: SubTask | None = None

        while True:
            if i >= len(p.allocations):
                break

            if execution_time == 0:
                break

            scheduled_task: SubTask = self.periodic_tasks[p.allocations[i][0]] if p.allocations[i][1] == -1 else \
                self.dags[p.allocations[i][1]].subtasks[p.allocations[i][0]]

            if p.allocations[i][4] <= start_time_temp:
                i += 1
                prev_scheduled_task = scheduled_task
                continue

            if p.allocations[i][3] >= start_time_temp + execution_time:
                index = i
                break

            elif p.allocations[i][3] > start_time_temp:
                execution_time = execution_time - (p.allocations[i][3] - start_time_temp)
                finish_time = p.allocations[i][3]
                if not only_check:
                    if prev_scheduled_task is None or prev_scheduled_task != task:
                        p.allocations.insert(i, [task_index, workflow_index,
                                                 job_index, start_time_temp, finish_time])
                        task.execution_times.append([p.index, start_time_temp, finish_time])
                        i = i + 1
                    else:
                        task.execution_times[-1][2] = finish_time
                        p.allocations[i - 1][4] = finish_time
                if only_check:
                    scheduled_task = task
                start_time_temp = p.allocations[i][3]

            elif p.allocations[i][3] == start_time_temp:
                if (not SchedulerPriority.bigger_than(task.task_type, scheduled_task.task_type,
                                                      task.deadline + task.arrival_time,
                                                      scheduled_task.deadline + scheduled_task.arrival_time)) and (
                        prev_scheduled_task is None or prev_scheduled_task != task or
                        self.preemption_type == PreemptionType.Eager):
                    start_time_temp = p.allocations[i][4]
                else:
                    finish_time = 0
                    if execution_time <= p.allocations[i][4] - start_time_temp:
                        finish_time = start_time_temp + execution_time
                        execution_time = 0
                    else:
                        finish_time = p.allocations[i][4]
                        execution_time = execution_time - (p.allocations[i][4] - start_time_temp)
                    if not only_check:
                        scheduled_task.remaining_execution_cost += p.get_execution_cost(
                            p.allocations[i][4] - start_time_temp
                        )
                        for e in range(len(scheduled_task.execution_times)):
                            if scheduled_task.execution_times[e][2] == p.allocations[i][4]:
                                del scheduled_task.execution_times[e]
                                break
                        self.scheduling_queue.put(
                            (scheduled_task.deadline + scheduled_task.arrival_time,
                             0, p.allocations[i][0], p.allocations[i][1], p.allocations[i][2])
                        )
                        del p.allocations[i]
                        if prev_scheduled_task is None or prev_scheduled_task != task:
                            p.allocations.insert(i, [task_index, workflow_index, job_index,
                                                     start_time_temp, finish_time])
                            task.execution_times.append([p.index, start_time_temp, finish_time])
                            i = i + 1
                        else:
                            task.execution_times[-1][2] = finish_time
                            p.allocations[i - 1][4] = finish_time
                    if only_check:
                        i = i + 1
                        scheduled_task = task
                    start_time_temp = finish_time

            else:
                if (not SchedulerPriority.bigger_than(task.task_type, scheduled_task.task_type,
                                                      task.deadline + task.arrival_time,
                                                      scheduled_task.deadline + scheduled_task.arrival_time)
                        or self.preemption_type == PreemptionType.Lazy):
                    start_time_temp = p.allocations[i][4]
                else:
                    finish_time = 0
                    if execution_time <= p.allocations[i][4] - start_time_temp:
                        finish_time = start_time_temp + execution_time
                        execution_time = 0
                    else:
                        finish_time = p.allocations[i][4]
                        execution_time = execution_time - (p.allocations[i][4] - start_time_temp)
                    if not only_check:
                        scheduled_task.remaining_execution_cost += p.get_execution_cost(
                            p.allocations[i][4] - start_time_temp
                        )
                        for e in scheduled_task.execution_times:
                            if e[2] == p.allocations[i][4]:
                                e[2] = start_time_temp
                                break
                        self.scheduling_queue.put(
                            (scheduled_task.deadline + scheduled_task.arrival_time,
                             0, p.allocations[i][0], p.allocations[i][1], p.allocations[i][2])
                        )
                        p.allocations[i][4] = start_time_temp
                        p.allocations.insert(i + 1,
                                             [task_index, workflow_index, job_index, start_time_temp, finish_time])
                        task.execution_times.append([p.index, start_time_temp, finish_time])
                        i = i + 2
                    if only_check:
                        i = i + 1
                        scheduled_task = task
                    start_time_temp = finish_time

        eft = start_time_temp + execution_time
        index = len(p.allocations) if index == -1 else index
        if execution_time != 0 and not only_check:
            prev_scheduled_task: SubTask | None = None if index == 0 else \
                self.periodic_tasks[p.allocations[index - 1][0]] if p.allocations[index - 1][1] == -1 else \
                    self.dags[p.allocations[index - 1][1]].subtasks[p.allocations[index - 1][0]]

            if prev_scheduled_task is None or prev_scheduled_task != task:
                p.allocations.insert(index, [task_index, workflow_index, job_index, start_time_temp, eft])
                task.execution_times.append([p.index, start_time_temp, eft])
            else:
                task.execution_times[-1][2] = eft
                p.allocations[index - 1][4] = eft

        if execution_time == 0 and not only_check and len(task.execution_times) == 0:
            task.execution_times.append([p.index, start_time_temp, start_time_temp])

        if not only_check:
            task.remaining_execution_cost = 0

        return eft

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
