import json

from Workflow.src.SubTask import TaskType, SubTask


class DAGSubTask(SubTask):

    def __init__(self, dag_id: int, subtask_id: int, task_type: TaskType):
        super().__init__(subtask_id, task_type)
        self.dag_id: int = dag_id
        self.label: int | None = None

    def set_label(self, label: int):
        self.label = label

    @staticmethod
    def generate(dag_id: int, subtask_id: int, task_type: TaskType,
                 memory_min: int, memory_max: int, execution_min: int, execution_max: int):
        task = DAGSubTask(dag_id, subtask_id, task_type)
        task.generate_memory(memory_min, memory_max)
        task.generate_execution_cost(execution_min, execution_max)
        return task


class DAGSubTaskEncoder(json.JSONEncoder):

    def default(self, obj: DAGSubTask):
        if isinstance(obj, DAGSubTask):
            return {
                'id': obj.id,
                'type': obj.task_type.name,
                'executionCost': obj.execution_cost,
                'memory': obj.memory,
            }
        return super().default(obj)
