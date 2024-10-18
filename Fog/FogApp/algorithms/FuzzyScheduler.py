import time
from queue import Queue
from threading import Lock

from ..types.Cloud import Cloud
from ..types.PreemptionType import PreemptionType
from ..types.Processor import Processor
from ..types.SubTask import SubTask


class FuzzyScheduler:
    def __init__(self, processors: list[Processor], time_scale: float, preemption_type: PreemptionType, cloud: Cloud):
        self.processors = processors
        self.start_time: float = 0
        self.time_scale = time_scale
        self.tasks: list[SubTask] = []
        self.preemption_type: PreemptionType = preemption_type
        self.cloud: Cloud = cloud

        self.scheduling_queue = Queue()
        self.backup_queue = Queue()
        self.queue_lock = Lock()

    def clear(self):
        self.queue_lock.acquire()
        self.tasks.clear()
        for processor in self.processors:
            processor.clear()
        self.scheduling_queue.queue.clear()
        self.backup_queue.queue.clear()

        self.queue_lock.release()

    def add_task(self, new_task: SubTask):
        self.queue_lock.acquire()
        new_task.index = len(self.tasks)
        self.tasks.append(new_task)
        new_task.arrival_time = int((time.time() - self.start_time) * self.time_scale * 1000)
        new_task.absolute_deadline = int((new_task.absolute_deadline_time - self.start_time) * self.time_scale * 1000)
        self.scheduling_queue.put(new_task.index)
        self.queue_lock.release()

    def schedule(self, current_time: int, total_time: int):
        self.queue_lock.acquire()
        q_size = self.scheduling_queue.qsize()
        for i in range(q_size):
            task_index = self.scheduling_queue.get()
            self.schedule_subtask(current_time, task_index)

        while not self.backup_queue.empty():
            self.scheduling_queue.put(self.backup_queue.get())

        for task in self.tasks:
            if ((not task.is_notify) and task.remaining_execution_cost == 0
                    and task.execution_times[-1][2] <= current_time):
                task.edge.notify(task.id, task.workflow_id, task.job_id)
                task.is_notify = True

        self.queue_lock.release()


    def schedule_subtask(self, start_time: int, task_index: int):
        candidate_processor: Processor | None = None
        task: SubTask = self.tasks[task_index]

        for p in self.processors:
            idle = self.check_processor(p, start_time, task_index, True)
            if idle:
                candidate_processor = p
                break

        fuzzy_value = self.fuzzy_offload_decision(task, candidate_processor, start_time)

        if fuzzy_value > 0.5 and task.execution_cost != 0:
            self.offload(0, task)
        else:
            if candidate_processor is None:
                self.backup_queue.put(task_index)
                return

            new_idle = self.check_processor(candidate_processor, start_time, task_index, False)
            if not new_idle:
                print("Warn")

    def check_processor(self, p: Processor, start_time: int, task_index: int, only_check: bool) -> int:

        task: SubTask = self.tasks[task_index]

        execution_time = p.get_execution_time(task.remaining_execution_cost)

        if len(p.allocations) > 0:
            if p.allocations[-1][2] > start_time:
                return False

        end_time = start_time + execution_time

        if not only_check:
            task.remaining_execution_cost = 0
            task.execution_times = [[p.index, start_time, end_time]]
            p.allocations.append([task_index, start_time, end_time])

        return True

    def offload(self, offload_index: int, task: SubTask):
        self.cloud.offload(task.edge.address, task)

    def fuzzy_offload_decision(self, task: SubTask, processor: Processor | None, current_time):
        """
        Fuzzy-based decision making for offloading a task.
        This function calculates fuzzy membership values based on deadline, and EFT.
        """
        deadline_fuzzy = self.fuzzy_deadline(task.absolute_deadline, task.arrival_time, current_time)
        eft_fuzzy = self.fuzzy_eft(processor, task.absolute_deadline, task.arrival_time, current_time,
                                   task.execution_cost)
        offload_fuzzy_value = (deadline_fuzzy * 0.5) + (eft_fuzzy * 0.5)
        return offload_fuzzy_value

    def fuzzy_deadline(self, deadline: int, arrival_time: int, current_time: int):
        remaining_time = deadline - current_time
        if remaining_time < (deadline - arrival_time) * 0.5:  # tight deadline
            return 1.0
        elif remaining_time < (deadline - arrival_time) * 0.7:
            return 0.6
        else:
            return 0.1

    def fuzzy_eft(self, processor: Processor | None, deadline: int, arrival_time: int,
                  current_time: int, execution_cost: int):
        if processor is None:
            return 0.6
        execution_time = processor.get_execution_time(execution_cost)

        eft = current_time + execution_time

        if eft > deadline:  # EFT exceeds deadline
            return 1.0
        elif eft > (deadline - arrival_time) * 0.7 + arrival_time:
            return 0.6
        else:
            return 0.1
