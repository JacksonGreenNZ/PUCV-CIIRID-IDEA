from abc import ABC, abstractmethod
from typing import List

from sopp.custom_dataclasses.facility import Facility
from sopp.custom_dataclasses.observation_target import ObservationTarget
from sopp.custom_dataclasses.position_time import PositionTime
from sopp.custom_dataclasses.time_window import TimeWindow


class ObservationPathFinder(ABC):
    '''
    The ObservationPathFinder determines the path the telescope will need to follow to track its target and returns
    a list of altitude, azimuth, and timestamp to represent the telescope's movement. It uses the observation
    target's right ascension and declination to determine this path.
    '''

    def __init__(self, facility: Facility, observation_target: ObservationTarget, time_window: TimeWindow):
        self._facility = facility
        self._observation_target = observation_target
        self._time_window = time_window

    @abstractmethod
    def calculate_path(self) -> List[PositionTime]:
        pass
