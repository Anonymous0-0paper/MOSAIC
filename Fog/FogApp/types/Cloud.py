import json
import threading

import requests

from ..types.SubTask import SubTask


class Cloud:

    def __init__(self, cloud_address):
        self.address = cloud_address

    def register(self, address: str, position_x: int, position_y: int, coverage_area: int):

        data = {
            "address": address,
            "positionX": position_x,
            "positionY": position_y,
            "coverageArea": coverage_area
        }

        url = f"http://{self.address}/CloudApp/Cloud/config/registerFog/"
        json_data = json.dumps(data)
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.post(url, data=json_data, headers=headers)

        if response.status_code == 200:
            print(f"Fog device successfully registered on the Cloud")
        else:
            print(f"Failed to submit data: {response.status_code}")

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

        url = f"http://{self.address}/CloudApp/Cloud/tasks/pushTask/"
        json_data = json.dumps(data)
        headers = {
            'Content-Type': 'application/json'
        }

        def request():
            response = requests.post(url, data=json_data, headers=headers)

            if response.status_code == 200:
                print(f"Task {task.id} | Job {task.job_id} | DAG {task.workflow_id} | D {task.absolute_deadline}"
                      f" submitted successfully on the Cloud {self.address}")
            else:
                print(f"Failed to submit data: {response.status_code}")

        _thread = threading.Thread(target=request, args=())
        _thread.start()
