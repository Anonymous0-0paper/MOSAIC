import json
import threading

import requests

from .Fog import Fog
from ..types.SubTask import SubTask


class Cloud:

    def __init__(self, cloud_address):
        self.address = cloud_address

    def get_nodes(self):
        url = f"http://{self.address}/CloudApp/Cloud/config/getNodes/"
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.get(url, headers=headers)
        fogs: list[Fog] = []

        if response.status_code == 200:
            response_json = response.json()
            for fog in response_json['fogs']:
                fogs.append(Fog(fog))

        else:
            print(f"Failed to get data from cloud: {url}")

        return fogs

    def register(self, back_address: str):

        data = {
            "address": back_address
        }

        url = f"http://{self.address}/CloudApp/Cloud/config/registerEdge/"
        json_data = json.dumps(data)
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.post(url, data=json_data, headers=headers)

        if response.status_code == 200:
            print(f"Edge device successfully registered on the Cloud")
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
                print(
                    f"Task {task.id} | Job {task.job_id} | DAG {task.workflow_id} | D {task.deadline + task.arrival_time}"
                    f" submitted successfully on the Cloud {self.address}")
            else:
                print(f"Failed to submit data: {response.status_code}")

        _thread = threading.Thread(target=request, args=())
        _thread.start()
