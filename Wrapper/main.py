import json
import os
import time

import requests

if __name__ == '__main__':

    cloud_address = os.getenv("CLOUD_ADDRESS")

    response = requests.get(f"http://{cloud_address}/CloudApp/Cloud/config/getNodes/")
    nodes = response.json()
    print("Edges", nodes["edges"])
    print("Fogs", nodes["fogs"])

    algorithms = ["MEES"]  # "MEES", "Random", "HEFT_EDF", "Fuzzy"
    tasks_loads = [f"load-{i}" for i in [4, 3, 2]]
    tasks_dominance = ["hard", "soft", "firm"]

    for load in tasks_loads:
        for dominance in tasks_dominance:
            for algorithm in algorithms:
                with open(f'tasks/{load}/{dominance}/dags.json', 'r') as file:
                    dags = json.load(file)
                with open(f'tasks/{load}/{dominance}/periodic_tasks.json', 'r') as file:
                    periodic_tasks = json.load(file)

                headers = {
                    'Content-Type': 'application/json'
                }

                # start the elements
                if True:
                    data = {
                        "algorithm": algorithm,
                        "outputName": f"{load}-{dominance}",
                    }
                    json_data = json.dumps(data)
                    requests.post(f"http://{cloud_address}/CloudApp/Cloud/config/start/",
                                  data=json_data, headers=headers)

                for i in range(len(nodes['fogs'])):
                    data = {
                        "algorithm": algorithm,
                        "outputName": f"{load}-{dominance}-{i}",
                    }
                    json_data = json.dumps(data)
                    requests.post(f"http://{nodes['fogs'][i]['address']}/FogApp/Fog/config/start/",
                                  data=json_data, headers=headers)

                for i in range(len(nodes['edges'])):
                    data = {
                        "algorithm": algorithm,
                        "outputName": f"{load}-{dominance}-{i}",
                    }
                    json_data = json.dumps(data)
                    requests.post(f"http://{nodes['edges'][i]['address']}/EdgeApp/Edge/config/start/",
                                  data=json_data, headers=headers)

                # submit the tasks
                for edge in nodes['edges']:
                    if True:
                        print("edge DAGs: ", edge['address'])
                        data = {
                            "dags": dags
                        }
                        url = f"http://{edge['address']}/EdgeApp/Edge/tasks/pushDAGs/"
                        json_data = json.dumps(data)
                        headers = {
                            'Content-Type': 'application/json'
                        }

                        requests.patch(url, headers=headers, data=json_data)
                    if True:
                        print("edge Periodics: ", edge['address'])
                        data = {
                            "tasks": periodic_tasks
                        }
                        url = f"http://{edge['address']}/EdgeApp/Edge/tasks/pushPeriodicTasks/"
                        json_data = json.dumps(data)
                        headers = {
                            'Content-Type': 'application/json'
                        }

                        requests.patch(url, headers=headers, data=json_data)

                time.sleep(800)
