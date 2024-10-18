from .SubTask import SubTask
from ..dtos.DAGSubTaskSerializer import DAGSubTaskSerializer


class DAGSubTask(SubTask):

    def __init__(self, dag_id: int, dto: DAGSubTaskSerializer):
        super().__init__(dto['id'], dto['type'], dto['executionCost'], dto['memory'])
        self.workflow_id: int = dag_id
