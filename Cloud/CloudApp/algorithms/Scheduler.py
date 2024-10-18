import math
import random
import time
from threading import Lock
from typing import Tuple

from ..types.PreemptionType import PreemptionType
from ..types.Processor import Processor
from ..types.SubTask import SubTask, TaskType


class Scheduler:
    def __init__(self, processors: list[Processor], time_scale: float, preemption_type: PreemptionType):
        self.processors = processors
        self.start_time: float | None = None
        self.time_scale: float = time_scale
        self.tasks: list[SubTask] = []
        self.ready_tasks_lock = Lock()
        self.ready_tasks = []
        self.preemption_type: PreemptionType = preemption_type
        self.need_schedule = False

        self.q_table = {}
        self.last_rewards = []
        self.last_rewards_index = 0
        self.last_rewards_total = 100
        self.action_n = {}

        self.alpha = 0.1  # Learning rate
        self.gamma = 0.9  # Discount factor
        self.epsilon = 0.99  # Exploration rate
        self.epsilon_decay = 0.99
        self.epsilon_min = 0.2
        self.num_episodes = 10  # Episode Numbers
        self.lam = 1.0  # Adaptive parameter

        self.reward_qos_sensitivity = 1.0
        self.reward_deadline_sensitivity = 1.0
        self.reward_qos_values: list[float] = []

    def clear(self):
        self.ready_tasks_lock.acquire()
        self.tasks.clear()
        for processor in self.processors:
            processor.clear()
        self.ready_tasks.clear()

        self.need_schedule = False

        self.q_table.clear()
        self.action_n.clear()

        self.alpha = 0.1
        self.gamma = 0.9
        self.epsilon = 0.99
        self.epsilon_decay = 0.99
        self.epsilon_min = 0.2
        self.num_episodes = 10
        self.lam = 1.0

        self.reward_qos_sensitivity = 1.0
        self.reward_deadline_sensitivity = 1.0
        self.reward_qos_values.clear()

        self.ready_tasks_lock.release()

    def add_task(self, new_task: SubTask):
        self.ready_tasks_lock.acquire()
        self.need_schedule = True
        new_task.index = len(self.tasks)
        self.tasks.append(new_task)
        new_task.arrival_time = int((time.time() - self.start_time) * self.time_scale * 1000)
        new_task.absolute_deadline = int((new_task.absolute_deadline_time - self.start_time) * self.time_scale * 1000)
        self.ready_tasks.append(new_task.index)
        self.ready_tasks_lock.release()

    def schedule(self, current_time: int, total_time: int):
        if current_time > total_time:
            print(".", end="")

        self.ready_tasks_lock.acquire()

        if self.need_schedule:
            self.schedule_rl(current_time)
            self.need_schedule = False

        i = 0
        while True:
            if i >= len(self.ready_tasks):
                break
            task = self.tasks[self.ready_tasks[i]]
            if task.remaining_execution_cost == 0 and task.execution_times[-1][2] <= current_time:
                task.edge.notify(task.id, task.workflow_id, task.job_id)
                del self.ready_tasks[i]
            else:
                i += 1

        self.ready_tasks_lock.release()

    def schedule_rl(self, current_time: int):
        print("Q-Table size: ", len(self.q_table))
        state_quantize = len(self.ready_tasks) % len(self.processors)

        for episode in range(self.num_episodes):
            self.reset_environment()

            ready_tasks_index = [
                task_index for task_index in self.ready_tasks if len(self.tasks[task_index].execution_times) == 0
            ]
            ready_tasks_type = [self.tasks[task_index].task_type for task_index in ready_tasks_index]
            ready_tasks_processor: list[int | None] = [None for _ in ready_tasks_index]

            state = (tuple(ready_tasks_type), tuple(ready_tasks_processor), state_quantize)

            while not self.is_terminal_state(state):

                # 0: ready task index, 1: processor index
                action: Tuple[int, int] | None = None
                actions = self.get_actions(state)

                # Epsilon-greedy action selection
                if random.uniform(0, 1) < self.epsilon:
                    # Exploration: choose a random action
                    action = self.random_action(actions)
                else:
                    # Exploitation: choose the action with the highest Q-value
                    action = self.ucb_action(state, actions, current_time)

                if action not in self.action_n:
                    self.action_n[action] = 1
                else:
                    self.action_n[action] += 1

                # take the action
                task = self.tasks[ready_tasks_index[action[0]]]
                selected_processor = self.processors[action[1]]
                execution_time = selected_processor.get_execution_time(task.remaining_execution_cost)
                start_time = current_time
                if len(selected_processor.temp_allocations) > 0:
                    start_time = max(start_time, selected_processor.temp_allocations[-1][2])
                selected_processor.temp_allocations.append([task.index, start_time, start_time + execution_time])
                task.temp_execution_times.append([action[1], start_time, start_time + execution_time])
                task.temp_remaining_execution_cost = 0

                reward = self.calculate_reward()

                # Define next state
                ready_tasks_processor[action[0]] = action[1]

                next_state = (tuple(ready_tasks_type), tuple(ready_tasks_processor), state_quantize)
                next_state_actions = self.get_actions(next_state)

                # Find max Q-value for next state
                next_q_values = [self.q_table[(next_state, a)] for a in next_state_actions]
                current_q = self.q_table[(state, action)]

                if len(next_q_values) > 0:
                    max_next_q = max(next_q_values)
                    # Update Q-value for the current state and action
                    self.q_table[(state, action)] = current_q + self.alpha * (
                            reward + self.gamma * max_next_q - current_q
                    )
                else:
                    self.q_table[(state, action)] = current_q + self.alpha * reward

                # go to next state
                state = next_state

                # update last rewards
                if len(self.last_rewards) == 0:
                    self.last_rewards = [reward for _ in range(self.last_rewards_total)]
                else:
                    self.last_rewards[self.last_rewards_index] = reward

                self.last_rewards_index += 1
                if self.last_rewards_index == self.last_rewards_total:
                    self.last_rewards_index = 0

                # update the lambda
                self.update_lambda()

            # Decay epsilon after each episode
            self.epsilon = max(self.epsilon * self.epsilon_decay, self.epsilon_min)

        for processor in self.processors:
            processor.apply_cache()

        for task_index in self.ready_tasks:
            task = self.tasks[task_index]
            task.apply_cache()

    def is_terminal_state(self, state: Tuple):
        for ready_task_processor in state[1]:
            if ready_task_processor is None:
                return False

        return True

    def get_actions(self, state: Tuple):
        actions = []

        for i in range(len(state[0])):
            if state[1][i] is None:
                for processor_index in range(len(self.processors)):
                    action = (i, processor_index)
                    actions.append(action)
                    if (state, action) not in self.q_table:
                        self.q_table[(state, action)] = 0.0
                    if action not in self.action_n:
                        self.action_n[action] = 0

        return actions

    def random_action(self, actions: list):
        return random.choice(actions)

    def ucb_action(self, state: Tuple, actions: list, current_time: int):
        max_ucb = - math.inf
        best_action = None

        for action in actions:
            if self.action_n[action] == 0:
                best_action = action
                break

            ucb = self.q_table[(state, action)] + self.lam * (
                math.sqrt(math.log(current_time) / self.action_n[action]))
            if ucb > max_ucb:
                max_ucb = ucb
                best_action = action

        return best_action

    def update_lambda(self):
        reward_mean = sum(self.last_rewards) / len(self.last_rewards)
        reward_variance = 0.0
        for reward in self.last_rewards:
            reward_variance += (reward - reward_mean) ** 2

        self.lam = 1 / (1 + (reward_variance / len(self.last_rewards)))

    def reset_environment(self):
        for processor in self.processors:
            processor.clear_cache()

        for task_index in self.ready_tasks:
            task = self.tasks[task_index]
            task.clear_cache()

    def calculate_reward(self):
        reward_deadline = 0.0

        qos = 0.0
        max_d = 0.0
        min_d = math.inf
        max_d_reward = -math.inf
        min_d_reward = math.inf

        for task_index in self.ready_tasks:
            task = self.tasks[task_index]
            if len(task.temp_execution_times) > 0:
                qos += self.qos(task)

                if task.temp_execution_times[-1][2] <= task.absolute_deadline:
                    c = task.temp_execution_times[-1][2] - task.arrival_time
                    d = task.absolute_deadline - task.arrival_time
                    reward_deadline_task = float(1 - ((c / d) ** self.reward_deadline_sensitivity))
                    if task.task_type == TaskType.FIRM:
                        reward_deadline_task *= 2
                    reward_deadline += reward_deadline_task
                    if reward_deadline_task > max_d_reward:
                        max_d_reward = reward_deadline_task
                    if reward_deadline_task < min_d_reward:
                        min_d_reward = reward_deadline_task
                    if d > max_d:
                        max_d = d
                    if d < min_d:
                        min_d = d

        qos = qos / len(self.ready_tasks)
        if len(self.reward_qos_values) > 100:
            del self.reward_qos_values[:50]
        self.reward_qos_values.append(qos)

        reward_qos_mean = sum(self.reward_qos_values) / len(self.reward_qos_values)
        reward_qos_mean_variance = 0.0
        for reward in self.reward_qos_values:
            reward_qos_mean_variance += (reward - reward_qos_mean) ** 2

        reward_qos_mu = math.sqrt(reward_qos_mean_variance)
        if reward_qos_mu != 0:
            self.reward_qos_sensitivity = reward_qos_mean / reward_qos_mu
            reward_qos = ((qos - reward_qos_mean) / reward_qos_mu) * (
                    1 - math.exp(-qos / self.reward_qos_sensitivity)
            )
        else:
            reward_qos = 0

        if max_d_reward != 0 and max_d > 2 * min_d:
            self.reward_deadline_sensitivity = math.log(max_d_reward / min_d_reward) / (
                math.log((max_d - min_d) / min_d)
            )

        return 0.5 * reward_qos + 0.5 * reward_deadline

    def qos(self, task: SubTask) -> float:
        ex_before_deadline = 0
        ex_after_deadline = task.temp_remaining_execution_cost

        if task.task_type == TaskType.FIRM:
            if len(task.temp_execution_times) == 0 or task.temp_execution_times[-1][2] > task.absolute_deadline:
                return 0
            return 1

        for ex in task.temp_execution_times:
            if ex[2] <= task.absolute_deadline:
                ex_before_deadline += self.processors[ex[0]].get_execution_cost(ex[2] - ex[1])
            elif ex[1] < task.absolute_deadline < ex[2]:
                ex_before_deadline += self.processors[ex[0]].get_execution_cost(task.absolute_deadline - ex[1])
                ex_after_deadline += self.processors[ex[0]].get_execution_cost(ex[2] - task.absolute_deadline)
            else:
                ex_after_deadline += self.processors[ex[0]].get_execution_cost(ex[2] - ex[1])

        if ex_before_deadline == 0:
            return 0

        return ex_before_deadline / (ex_after_deadline + ex_before_deadline)

    def reset_tasks(self, current_time: int):
        for p in self.processors:
            e = 0
            while True:
                if e == len(p.allocations):
                    break
                else:
                    if p.allocations[e][1] > current_time + 10000:
                        del p.allocations[e]
                    else:
                        e += 1

        for task_index in self.ready_tasks:
            task = self.tasks[task_index]
            e = 0
            while True:
                if e == len(task.execution_times):
                    break
                else:
                    if task.execution_times[e][1] > current_time + 10000:
                        p = self.processors[task.execution_times[e][0]]
                        task.remaining_execution_cost += p.get_execution_cost(
                            task.execution_times[e][2] - task.execution_times[e][1])
                        del task.execution_times[e]
                    else:
                        e += 1
