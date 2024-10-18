import math


class Processor:

    def __init__(self, index: int, frequency: float, memory: int, active_power: float, idle_power: float):
        self.index = index
        self.frequency: float = frequency  # GHz
        self.memory: int = memory  # KB
        self.active_power: float = active_power  # W
        self.idle_power: float = idle_power  # W

        # [0: task index, 1: workflow index, 2: job index 3: start time, 4: end time]
        self.allocations: list[list[int]] = []

    def get_execution_time(self, execution_cost: int) -> int:
        '''
        Returns the execution time of the task at this processor in milliseconds.
        '''
        return math.ceil(execution_cost / self.frequency)

    def get_execution_cost(self, execution_time) -> int:
        return int(self.frequency * execution_time)

    def clear(self):
        self.allocations.clear()
