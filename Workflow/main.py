import math
import os
import random

from Workflow.src.DAG.DAG import DAG
from Workflow.src.DAG.FFT import FFT
from Workflow.src.DAG.FullTopologyDAG import FullTopologyDAG
from Workflow.src.DAG.GE import GE
from Workflow.src.PeriodicTask import PeriodicTask
from Workflow.src.SubTask import TaskType

if __name__ == '__main__':
    show_dag = int(os.environ.get('SHOW_DAG', 0)) == 1

    # Periodic Type Arguments
    periodic_hard_count = int(os.environ.get('PERIODIC_HARD_COUNT', 10))
    periodic_hard_computation_min = int(os.environ.get('PERIODIC_HARD_COMPUTATION_MIN', 1000))
    periodic_hard_computation_max = int(os.environ.get('PERIODIC_HARD_COMPUTATION_MAX', 5000))
    periodic_hard_deadline_min = int(os.environ.get('PERIODIC_HARD_DEADLINE_MIN', 500))
    periodic_hard_deadline_max = int(os.environ.get('PERIODIC_HARD_DEADLINE_MAX', 2000))
    periodic_hard_memory_min = int(os.environ.get('PERIODIC_HARD_MEMORY_MIN', 20))
    periodic_hard_memory_max = int(os.environ.get('PERIODIC_HARD_MEMORY_MAX', 100))

    periodic_firm_count = int(os.environ.get('PERIODIC_FIRM_COUNT', 10))
    periodic_firm_computation_min = int(os.environ.get('PERIODIC_FIRM_COMPUTATION_MIN', 1000))
    periodic_firm_computation_max = int(os.environ.get('PERIODIC_FIRM_COMPUTATION_MAX', 5000))
    periodic_firm_deadline_min = int(os.environ.get('PERIODIC_FIRM_DEADLINE_MIN', 500))
    periodic_firm_deadline_max = int(os.environ.get('PERIODIC_FIRM_DEADLINE_MAX', 2000))
    periodic_firm_memory_min = int(os.environ.get('PERIODIC_FIRM_MEMORY_MIN', 20))
    periodic_firm_memory_max = int(os.environ.get('PERIODIC_FIRM_MEMORY_MAX', 100))

    periodic_soft_count = int(os.environ.get('PERIODIC_SOFT_COUNT', 10))
    periodic_soft_computation_min = int(os.environ.get('PERIODIC_SOFT_COMPUTATION_MIN', 1000))
    periodic_soft_computation_max = int(os.environ.get('PERIODIC_SOFT_COMPUTATION_MAX', 5000))
    periodic_soft_deadline_min = int(os.environ.get('PERIODIC_SOFT_DEADLINE_MIN', 500))
    periodic_soft_deadline_max = int(os.environ.get('PERIODIC_SOFT_DEADLINE_MAX', 2000))
    periodic_soft_memory_min = int(os.environ.get('PERIODIC_SOFT_MEMORY_MIN', 20))
    periodic_soft_memory_max = int(os.environ.get('PERIODIC_SOFT_MEMORY_MAX', 100))

    # DAG Type Arguments
    dag_type = os.environ.get('DAG_TYPE', 'Random')  # FFT | GE | FullTopology | Random

    dag_hard_size: int = int(os.environ.get('DAG_HARD_SIZE', 20))
    dag_hard_count = int(os.environ.get('DAG_HARD_COUNT', 1))
    dag_hard_communication_min: int = int(os.environ.get('DAG_HARD_COMMUNICATION_MIN', 1))
    dag_hard_communication_max: int = int(os.environ.get('DAG_HARD_COMMUNICATION_MAX', 20))
    dag_hard_computation_min = int(os.environ.get('DAG_HARD_COMPUTATION_MIN', 1000))
    dag_hard_computation_max = int(os.environ.get('DAG_HARD_COMPUTATION_MAX', 5000))
    dag_hard_deadline_min = int(os.environ.get('DAG_HARD_DEADLINE_MIN', 500))
    dag_hard_deadline_max = int(os.environ.get('DAG_HARD_DEADLINE_MAX', 2000))
    dag_hard_memory_min = int(os.environ.get('DAG_HARD_MEMORY_MIN', 20))
    dag_hard_memory_max = int(os.environ.get('DAG_HARD_MEMORY_MAX', 100))
    dag_hard_arrival_scale = float(os.environ.get('DAG_HARD_ARRIVAL_SCALE', 10000))

    dag_firm_size: int = int(os.environ.get('DAG_FIRM_SIZE', 20))
    dag_firm_count = int(os.environ.get('DAG_FIRM_COUNT', 1))
    dag_firm_communication_min: int = int(os.environ.get('DAG_FIRM_COMMUNICATION_MIN', 1))
    dag_firm_communication_max: int = int(os.environ.get('DAG_FIRM_COMMUNICATION_MAX', 20))
    dag_firm_computation_min = int(os.environ.get('DAG_FIRM_COMPUTATION_MIN', 1000))
    dag_firm_computation_max = int(os.environ.get('DAG_FIRM_COMPUTATION_MAX', 5000))
    dag_firm_deadline_min = int(os.environ.get('DAG_FIRM_DEADLINE_MIN', 500))
    dag_firm_deadline_max = int(os.environ.get('DAG_FIRM_DEADLINE_MAX', 2000))
    dag_firm_memory_min = int(os.environ.get('DAG_FIRM_MEMORY_MIN', 20))
    dag_firm_memory_max = int(os.environ.get('DAG_FIRM_MEMORY_MAX', 100))
    dag_firm_arrival_scale = float(os.environ.get('DAG_FIRM_ARRIVAL_SCALE', 10000))

    dag_soft_size: int = int(os.environ.get('DAG_SOFT_SIZE', 20))
    dag_soft_count = int(os.environ.get('DAG_SOFT_COUNT', 1))
    dag_soft_communication_min: int = int(os.environ.get('DAG_SOFT_COMMUNICATION_MIN', 1))
    dag_soft_communication_max: int = int(os.environ.get('DAG_SOFT_COMMUNICATION_MAX', 20))
    dag_soft_computation_min = int(os.environ.get('DAG_SOFT_COMPUTATION_MIN', 1000))
    dag_soft_computation_max = int(os.environ.get('DAG_SOFT_COMPUTATION_MAX', 5000))
    dag_soft_deadline_min = int(os.environ.get('DAG_SOFT_DEADLINE_MIN', 500))
    dag_soft_deadline_max = int(os.environ.get('DAG_SOFT_DEADLINE_MAX', 2000))
    dag_soft_memory_min = int(os.environ.get('DAG_SOFT_MEMORY_MIN', 20))
    dag_soft_memory_max = int(os.environ.get('DAG_SOFT_MEMORY_MAX', 100))
    dag_soft_arrival_scale = float(os.environ.get('DAG_SOFT_ARRIVAL_SCALE', 10000))

    # create periodic hard tasks
    periodic_tasks: list[PeriodicTask] = []
    periodic_index = -1
    for i in range(periodic_hard_count):
        periodic_index += 1
        periodic_tasks.append(PeriodicTask.generate(periodic_index, TaskType.HARD,
                                                    periodic_hard_memory_min, periodic_hard_memory_max,
                                                    periodic_hard_computation_min, periodic_hard_computation_max,
                                                    periodic_hard_deadline_min, periodic_hard_deadline_max))
    # create periodic firm tasks
    for i in range(periodic_firm_count):
        periodic_index += 1
        periodic_tasks.append(PeriodicTask.generate(periodic_index, TaskType.FIRM,
                                                    periodic_firm_memory_min, periodic_firm_memory_max,
                                                    periodic_firm_computation_min, periodic_firm_computation_max,
                                                    periodic_firm_deadline_min, periodic_firm_deadline_max))
    # create periodic soft tasks
    for i in range(periodic_soft_count):
        periodic_index += 1
        periodic_tasks.append(PeriodicTask.generate(periodic_index, TaskType.SOFT,
                                                    periodic_soft_memory_min, periodic_soft_memory_max,
                                                    periodic_soft_computation_min, periodic_soft_computation_max,
                                                    periodic_soft_deadline_min, periodic_soft_deadline_max))
    # create aperiodic hard tasks
    dags: list[DAG] = []
    dag_index = -1
    for i in range(dag_hard_count):
        dag_index += 1
        dag_type_selected = dag_type
        if dag_type_selected == "Random":
            dag_type_selected = random.choice(['FFT', 'GE', 'FullTopology'])

        if dag_type_selected == 'FFT':
            dags.append(FFT.generate_dag(dag_index, dag_hard_size, TaskType.HARD, dag_hard_arrival_scale,
                                         dag_hard_memory_min, dag_hard_memory_max, dag_hard_computation_min,
                                         dag_hard_computation_max, dag_hard_deadline_min, dag_hard_deadline_max,
                                         dag_hard_communication_min, dag_hard_communication_max))
        elif dag_type_selected == 'GE':
            dags.append(GE.generate_dag(dag_index, dag_hard_size, TaskType.HARD, dag_hard_arrival_scale,
                                        dag_hard_memory_min, dag_hard_memory_max, dag_hard_computation_min,
                                        dag_hard_computation_max, dag_hard_deadline_min, dag_hard_deadline_max,
                                        dag_hard_communication_min, dag_hard_communication_max))
        else:
            dags.append(
                FullTopologyDAG.generate_dag(dag_index, dag_hard_size, TaskType.HARD, dag_hard_arrival_scale,
                                             dag_hard_memory_min, dag_hard_memory_max,
                                             dag_hard_computation_min, dag_hard_computation_max,
                                             dag_hard_deadline_min, dag_hard_deadline_max,
                                             dag_hard_communication_min, dag_hard_communication_max,
                                             int(math.sqrt(dag_hard_size) // 2), int(math.sqrt(dag_hard_size)),
                                             int(math.sqrt(dag_hard_size)), int(math.sqrt(dag_hard_size)) * 2,
                                             1, int(math.sqrt(dag_hard_size)) * 2,
                                             [-1, -1, -1]))

    # create aperiodic firm tasks
    for i in range(dag_firm_count):
        dag_index += 1
        dag_type_selected = dag_type
        if dag_type_selected == "Random":
            dag_type_selected = random.choice(['FFT', 'GE', 'FullTopology'])

        if dag_type_selected == 'FFT':
            dags.append(FFT.generate_dag(dag_index, dag_firm_size, TaskType.FIRM, dag_firm_arrival_scale,
                                         dag_firm_memory_min, dag_firm_memory_max, dag_firm_computation_min,
                                         dag_firm_computation_max, dag_firm_deadline_min, dag_firm_deadline_max,
                                         dag_firm_communication_min, dag_firm_communication_max))
        elif dag_type_selected == 'GE':
            dags.append(GE.generate_dag(dag_index, dag_firm_size, TaskType.FIRM, dag_firm_arrival_scale,
                                        dag_firm_memory_min, dag_firm_memory_max, dag_firm_computation_min,
                                        dag_firm_computation_max, dag_firm_deadline_min, dag_firm_deadline_max,
                                        dag_firm_communication_min, dag_firm_communication_max))
        else:
            dags.append(FullTopologyDAG.generate_dag(dag_index, dag_firm_size, TaskType.FIRM, dag_firm_arrival_scale,
                                                     dag_firm_memory_min, dag_firm_memory_max,
                                                     dag_firm_computation_min, dag_firm_computation_max,
                                                     dag_firm_deadline_min, dag_firm_deadline_max,
                                                     dag_firm_communication_min, dag_firm_communication_max,
                                                     int(math.sqrt(dag_firm_size) // 2), int(math.sqrt(dag_firm_size)),
                                                     int(math.sqrt(dag_firm_size)), int(math.sqrt(dag_firm_size)) * 2,
                                                     1, int(math.sqrt(dag_firm_size)) * 2,
                                                     [-1, -1, -1]))

    # create aperiodic soft tasks
    for i in range(dag_soft_count):
        dag_index += 1
        dag_type_selected = dag_type
        if dag_type_selected == "Random":
            dag_type_selected = random.choice(['FFT', 'GE', 'FullTopology'])

        if dag_type_selected == 'FFT':
            dags.append(FFT.generate_dag(dag_index, dag_soft_size, TaskType.SOFT, dag_soft_arrival_scale,
                                         dag_soft_memory_min, dag_soft_memory_max, dag_soft_computation_min,
                                         dag_soft_computation_max, dag_soft_deadline_min, dag_soft_deadline_max,
                                         dag_soft_communication_min, dag_soft_communication_max))
        elif dag_type_selected == 'GE':
            dags.append(GE.generate_dag(dag_index, dag_soft_size, TaskType.SOFT, dag_soft_arrival_scale,
                                        dag_soft_memory_min, dag_soft_memory_max, dag_soft_computation_min,
                                        dag_soft_computation_max, dag_soft_deadline_min, dag_soft_deadline_max,
                                        dag_soft_communication_min, dag_soft_communication_max))
        else:
            dags.append(FullTopologyDAG.generate_dag(dag_index, dag_soft_size, TaskType.SOFT, dag_soft_arrival_scale,
                                                     dag_soft_memory_min, dag_soft_memory_max,
                                                     dag_soft_computation_min, dag_soft_computation_max,
                                                     dag_soft_deadline_min, dag_soft_deadline_max,
                                                     dag_soft_communication_min, dag_soft_communication_max,
                                                     int(math.sqrt(dag_soft_size) // 2), int(math.sqrt(dag_soft_size)),
                                                     int(math.sqrt(dag_soft_size)), int(math.sqrt(dag_soft_size)) * 2,
                                                     1, int(math.sqrt(dag_soft_size)) * 2,
                                                     [-1, -1, -1]))

    DAG.store(dags, "./Tasks/dags.json")
    PeriodicTask.store(periodic_tasks, "./Tasks/periodic_tasks.json")

    if show_dag:
        for dag in dags:
            dag.show(False)