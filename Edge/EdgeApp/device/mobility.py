from enum import Enum

import numpy as np
from scipy.stats import levy


class WalkMode(Enum):
    Random = "Random"
    Levy = "Levy"


def random_walk(steps: int = 1, start_position: tuple[int, int] = (0, 0), max_position: tuple[int, int] = (1000, 1000)) -> \
tuple[int, int]:
    """
    Simulates a 2D random walk.

    Parameters:
    steps (int): The number of steps to take in the random walk.
    start_position (tuple): The starting position of the random walk (default is (0, 0)).
    max_position (tuple): The maximum allowed position of the random walk (default is (1000, 1000)).

    Returns:
    The last position of the random walk.
    """
    last_position: tuple[int, int] = (start_position[0], start_position[1])

    for _ in range(steps):
        dx = np.random.choice([-1, 0, 1])
        dy = np.random.choice([-1, 0, 1])
        new_x = int(min(max(last_position[0] + dx, 0), max_position[0]))
        new_y = int(min(max(last_position[1] + dy, 0), max_position[1]))
        last_position = (new_x, new_y)

    return last_position


def levy_walk(steps: int = 1, start_position: tuple[int, int] = (0, 0), max_position: tuple[int, int] = (1000, 1000),
              scale: float = 2, location: float = 0) -> tuple[int, int]:
    """
    Simulates a 2D Lévy walk.

    Parameters:
    steps (int): The number of steps to take in the Lévy walk.
    start_position (tuple): The starting position of the Lévy walk (default is (0, 0)).
    max_position (tuple): The maximum allowed position of the random walk (default is (1000, 1000)).
    scale (float): The scale parameter of the Lévy distribution (default is 1).
    location (float): The location parameter of the Lévy distribution (default is 0).

    Returns:
    The last position of the random walk.
    """
    last_position: tuple[int, int] = (start_position[0], start_position[1])

    for _ in range(steps):
        # Generate a random step length from the Levy distribution
        step_length = levy.rvs(scale=scale, loc=location)

        # Generate a random direction
        theta = np.random.uniform(0, 2 * np.pi)
        dx = step_length * np.cos(theta)
        dy = step_length * np.sin(theta)

        new_x = int(min(max(last_position[0] + dx, 0), max_position[0]))
        new_y = int(min(max(last_position[1] + dy, 0), max_position[1]))
        last_position = (new_x, new_y)

    return last_position
