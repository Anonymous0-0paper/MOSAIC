import random
import time
from threading import Lock

from ..types.PreemptionType import PreemptionType
from ..types.Processor import Processor
from ..types.SubTask import SubTask


class RandomScheduler:
    def __init__(self, processors: list[Processor], time_scale: float, preemption_type: PreemptionType):
        self.processors = processors
        self.start_time: float = 0
        self.time_scale = time_scale
        self.tasks: list[SubTask] = []
        self.ready_tasks_lock = Lock()
        self.ready_tasks: list[int] = []
        self.preemption_type: PreemptionType = preemption_type

    def clear(self):
        self.ready_tasks_lock.acquire()
        self.tasks.clear()
        for processor in self.processors:
            processor.clear()
        self.ready_tasks.clear()

        self.ready_tasks_lock.release()

    def add_task(self, new_task: SubTask):
        self.ready_tasks_lock.acquire()
        new_task.index = len(self.tasks)
        self.tasks.append(new_task)
        new_task.arrival_time = int((time.time() - self.start_time) * self.time_scale * 1000)
        new_task.absolute_deadline = int((new_task.absolute_deadline_time - self.start_time) * self.time_scale * 1000)
        self.ready_tasks.append(new_task.index)
        self.ready_tasks_lock.release()

    def schedule(self, current_time: int, total_time: int):
        self.ready_tasks_lock.acquire()

        max_checked = 100
        checked = 0
        while True:
            if len(self.ready_tasks) == 0 or checked == max_checked:
                break

            selected_index = random.randint(0, len(self.ready_tasks) - 1)
            selected_ready_task = self.ready_tasks[selected_index]
            selected_task: SubTask = self.tasks[selected_ready_task]

            if current_time < selected_task.arrival_time:
                checked += 1
                continue

            self.schedule_subtask(current_time, selected_ready_task)
            del self.ready_tasks[selected_index]

        for task in self.tasks:
            if ((not task.is_notify) and task.remaining_execution_cost == 0
                    and task.execution_times[-1][2] <= current_time):
                task.edge.notify(task.id, task.workflow_id, task.job_id)
                task.is_notify = True

        self.ready_tasks_lock.release()

    def schedule_subtask(self, start_time: int, task_index: int):
        task: SubTask = self.tasks[task_index]

        processor_index = random.randint(0, len(self.processors) - 1)
        if len(self.processors[processor_index].allocations) > 0:
            start_time = max(start_time, self.processors[processor_index].allocations[-1][2])

        end_time = start_time + self.processors[processor_index].get_execution_time(task.execution_cost)

        task.remaining_execution_cost = 0
        task.execution_times = [[processor_index, start_time, end_time]]
        self.processors[processor_index].allocations.append([task_index, start_time, end_time])