from dataclasses import dataclass
from typing import Optional


@dataclass
class Position:
    """
    Represents a position relative to an observer on Earth.

    Attributes:
    + altitude (float): The altitude angle of the object in degrees. It ranges
      from 0° at the horizon to 90° directly overhead at the zenith. A negative
      altitude means the satellite is below the horizon.
    + azimuth (float): The azimuth angle of the object in degrees, measured
      clockwise around the horizon. It runs from 0° (geographic north) through
      east (90°), south (180°), and west (270°) before returning to the north.
    + distance (Optional[float]): The straight-line distance between the
      object and the observer in kilometers. If not provided, it is set to
      None.
    """
    altitude: float
    azimuth: float
    distance_km: Optional[float] = None
