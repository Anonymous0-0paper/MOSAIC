import json
import random

from Workflow.src.SubTask import SubTask, TaskType


class PeriodicTask(SubTask):

    def __init__(self, task_id: int, task_type: TaskType):
        super().__init__(task_id, task_type)
        self.deadline: int | None = None

    def generate_deadline(self, deadline_min: int, deadline_max: int):
        self.deadline = random.randint(deadline_min, deadline_max)

    @staticmethod
    def generate(task_id: int, task_type: TaskType, memory_min: int, memory_max: int,
                 execution_min: int, execution_max: int, deadline_min: int, deadline_max: int):
        task = PeriodicTask(task_id, task_type)
        task.generate_memory(memory_min, memory_max)
        task.generate_execution_cost(execution_min, execution_max)
        task.generate_deadline(deadline_min, deadline_max)

        return task

    @staticmethod
    def store(tasks, file_path: str = "./Examples/periodic_tasks.json"):
        tasks_json = json.dumps(tasks, indent=4, cls=PeriodicTaskEncoder)

        with open(file_path, "w") as file:
            file.write(tasks_json)


class PeriodicTaskEncoder(json.JSONEncoder):

    def default(self, obj: PeriodicTask):
        if isinstance(obj, PeriodicTask):
            return {
                'id': obj.id,
                'type': obj.task_type.name,
                'executionCost': obj.execution_cost,
                'memory': obj.memory,
                'deadline': obj.deadline
            }
        return super().default(obj)
