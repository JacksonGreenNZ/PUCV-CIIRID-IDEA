from dataclasses import dataclass, field
from operator import attrgetter
from typing import List
from sopp.custom_dataclasses.satellite.satellite import Satellite
from sopp.custom_dataclasses.time_window import TimeWindow
from sopp.custom_dataclasses.position_time import PositionTime

'''
OverheadWindow class is designed to store the time windows that a given satellite is overhead and includes the Satellite object,
as well as a TimeWindow object that contains the interference start and end times.

  + satellite:      the Satellite that is overhead during the time window.
  + positions:      a list of PositionTimes of the satellite while within the main beam
  + overhead_time:  a property TimeWindow representing the time the satellite enters and exits view.
'''

@dataclass
class OverheadWindow:
    satellite: Satellite
    positions: List[PositionTime] = field(default_factory=list)

    def __post_init__(self):
        self.positions.sort(key=attrgetter('time'))

    @property
    def overhead_time(self):
        if not self.positions:
            return None
        begin = self.positions[0].time
        end = self.positions[-1].time
        return TimeWindow(begin=begin, end=end)
