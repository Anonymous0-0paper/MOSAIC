import json
import threading

import requests

from ..dtos.EdgeSerializer import EdgeSerializer


class Edge:
    def __init__(self, dto: EdgeSerializer):
        self.address = dto['address']

    def notify(self, task_id: int, workflow_id: int, job_id: int):

        data = {
            "taskId": task_id,
            "workflowId": workflow_id,
            "jobId": job_id
        }

        url = f"http://{self.address}/EdgeApp/Edge/tasks/notifyExecuteTask/"
        json_data = json.dumps(data)
        headers = {
            'Content-Type': 'application/json'
        }

        def request():
            try:
                response = requests.patch(url, data=json_data, headers=headers)

                if response.status_code == 200:
                    print(f"Data successfully back to the Edge {self.address}")
                else:
                    print(f"Failed to submit data: {response.status_code}")
            except Exception as e:
                print(f"Failed to submit data: {e}")

        _thread = threading.Thread(target=request, args=())
        _thread.start()
