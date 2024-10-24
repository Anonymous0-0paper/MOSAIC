# MEES
## Overview

This project implements a Kubernetes-managed, Django-based architecture designed for task offloading and scheduling across Cloud, Edge, Fog, and IoT clusters. The system is structured to manage IoT devices (acting as pods) and process the tasks they generate, whether they are periodic or dependent (in Directed Acyclic Graphs, DAGs). 

![MEES framework overview](./Results/system.svg)

### Key Components:

1. **IoT Cluster**:
   - Contains multiple pods representing IoT devices such as sensors.
   - Each device generates various tasks, which may be periodic or have dependencies (DAG-based).
   - A controller unit on each device selects the appropriate node (Edge, Fog, or Cloud) to perform the tasks.

2. **Edge Cluster**:
   - Comprises several edge devices, each containing:
     - **Task Handler**: Handles task input/output and execution.
     - **Scheduler**: Manages task scheduling.
     - **Offload Control Unit**: Manages the offloading of tasks to other nodes.
     - **Mobility Control Unit**: Handles the mobility of devices, managing changes in their location.

3. **Fog Cluster**:
   - Contains fog devices equipped with:
     - **Task Handler**: Responsible for task execution.
     - **Offload Control Unit**: Manages task offloading.
     - **Reinforcement Learning (RL) Scheduler**: Optimizes task execution and management based on historical performance.

4. **Cloud Cluster**:
   - Includes a pod with:
     - **Task Handler**: Executes and manages tasks.
     - **RL Scheduler**: Coordinates resource management and task scheduling.
     - **Device Registry Unit**: Registers and manages both edge and fog devices.

5. **Monitoring Unit**:
   - The system is equipped with a monitoring unit that tracks key metrics such as:
     - Latency
     - Energy consumption
     - Resource utilization
   - All data and task metadata are stored in a central database.

This architecture allows dynamic task allocation, mobility handling, and efficient resource usage across a heterogeneous distributed network of IoT, Edge, Fog, and Cloud layers.

---

## Quick Start

This guide will help you quickly set up and run the project using Python 3.12 in a Linux environment.

### Prerequisites

- **Python 3.12** or higher
- **Bash** shell
- Kubernetes environment with appropriate clusters (IoT, Edge, Fog, Cloud)
- Docker (for containerized deployments)
- Kubernetes command-line tool (`kubectl`)

### Setup

1. **Clone the repository**:

   ```bash
   git [clone https://github.com/Anonymous0-0paper/MEES.git]
   cd MEES

2. **Install dependencies**:

   Make sure you have Python 3.12 installed. Then, install the required Python packages using:

   ```bash
   pip install -r requirements.txt

3. **Run setup script**:

    The provided `bash.sh` script will help set up the environment and deploy the required services.

   ```bash
   ./bash.sh

## Kubernetizing the System

To deploy the architecture on Kubernetes, you need to deploy each cluster (IoT, Edge, Fog, Cloud) with its specific deployment and service configurations. The deployment and service YAML files are located within the respective directories of the clusters (IoT, Edge, Fog, and Cloud).

### Deploying IoT Cluster

1. **Deployment**:
   Modify and apply the provided `iot-deployment.yaml` file in the `IoT` directory.

   ```bash
   kubectl apply -f IoT/iot-deployment.yaml

2. **Service**:
   Deploy the service configuration for IoT devices:

   ```bash
   kubectl apply -f IoT/iot-service.yaml

### Deploying Edge Cluster

For the `Edge` Cluster, navigate to the Edge directory and deploy the relevant files:

1. **Deployment**:
   ```bash
   kubectl apply -f Edge/edge-deployment.yaml

2. **Service**:

   ```bash
   kubectl apply -f Edge/edge-service.yaml

### Deploying Fog Cluster

Navigate to the `Fog` directory and apply the respective files for the Fog Cluster:

1. **Deployment**:
   ```bash
   kubectl apply -f Fog/fog-deployment.yaml

2. **Service**:

   ```bash
   kubectl apply -f Fog/fog-service.yaml

### Deploying Cloud Cluster

Finally, navigate to the `Cloud` directory and deploy the Cloud Cluster using the following commands:

1. **Deployment**:
   ```bash
   kubectl apply -f Cloud/cloud-deployment.yaml

2. **Service**:

   ```bash
   kubectl apply -f Cloud/cloud-service.yaml

## Experiments

The results of our experiments are available in the `Results` directory. Each experiment was conducted with different configurations, showcasing the performance under various setups.

- **Experiment Configurations**: Configurations are found under:
  - `Results/config-1/`
  - `Results/config-2/`
  - `Results/config-3/`
  - `Results/config-4/`
  - `Results/config-5/`

To see detailed results, refer to the corresponding PDFs in each folder.

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.
