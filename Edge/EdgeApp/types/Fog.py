import json
import math
import threading

import requests

from ..dtos.FogSerializer import FogSerializer
from ..types.SubTask import SubTask


class Fog:

    def __init__(self, dto: FogSerializer):
        self.address = dto['address']
        self.position_x: int = dto['positionX']
        self.position_y: int = dto['positionY']
        self.coverage_area = dto['coverageArea']

    def is_in_range(self, position_x: int, position_y: int) -> bool:
        if self.distance(position_x, position_y) <= self.coverage_area:
            return True

        return False

    def distance(self, position_x: int, position_y: int) -> int:
        dis = (self.position_x - position_x) ** 2 + (self.position_y - position_y) ** 2
        dis = math.ceil(math.sqrt(dis))
        return dis

    def offload(self, back_address: str, task: SubTask):

        data = {
            "task": {
                "id": task.id,
                "workflowId": task.workflow_id,
                "jobId": task.job_id,
                "type": task.task_type.name,
                "executionCost": task.execution_cost,
                "memory": task.memory,
                "absoluteDeadline": task.absolute_deadline
            },
            "edgeAddress": back_address,
        }

        url = f"http://{self.address}/FogApp/Fog/tasks/pushTask/"
        json_data = json.dumps(data)
        headers = {
            'Content-Type': 'application/json'
        }

        def request():
            response = requests.post(url, data=json_data, headers=headers)

            if response.status_code == 200:
                print(
                    f"Task {task.id} | Job {task.job_id} | DAG {task.workflow_id} | D {task.deadline + task.arrival_time}"
                    f" submitted successfully on the Fog {self.address}")
            else:
                print(f"Failed to submit data: {response.status_code}")

        _thread = threading.Thread(target=request, args=())
        _thread.start()
