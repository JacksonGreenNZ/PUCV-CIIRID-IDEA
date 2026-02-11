from dataclasses import dataclass


@dataclass
class MeanMotion:
    """
    Represents the mean motion of a satellite in radians per minute.

    Attributes:
    - first_derivative (float): The first derivative of the mean motion.
    - second_derivative (float): The second derivative of the mean motion.
    - value (float): The actual mean motion value in radians per minute.
    """

    first_derivative: float
    second_derivative: float
    value: float
