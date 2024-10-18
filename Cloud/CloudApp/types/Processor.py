import math


class Processor:

    def __init__(self, index: int, frequency: float, memory: int, active_power: float, idle_power: float):
        self.index = index
        self.frequency: float = frequency  # GHz
        self.memory: int = memory  # KB
        self.active_power: float = active_power  # W
        self.idle_power: float = idle_power  # W

        # [0: task index, 1: start time, 2: end time]
        self.allocations: list[list[int]] = []
        self.temp_allocations: list[list[int]] = []

    def get_execution_time(self, execution_cost: int) -> int:
        '''
        Returns the execution time of the task at this processor in milliseconds.
        '''
        return math.ceil(execution_cost / self.frequency)

    def get_execution_cost(self, execution_time) -> int:
        return int(self.frequency * execution_time)

    def clear(self):
        self.allocations.clear()

    def clear_cache(self):
        self.temp_allocations = [item for item in self.allocations]

    def apply_cache(self):
        self.allocations = [item for item in self.temp_allocations]
