from dataclasses import dataclass, field

from sopp.custom_dataclasses.facility import Facility
from sopp.custom_dataclasses.frequency_range.frequency_range import FrequencyRange
from sopp.custom_dataclasses.time_window import TimeWindow

'''
The Reservation class stores the Facility, as well as some additional reservation-specific information, such as reservation start and end times.
  + facility:   Facility object with RA facility and observation parameters
  + time:       TimeWindow that represents the start and end time of the ideal reservation.
  + frequency:  FrequencyRange of the requested observation. This is the frequency that the RA telescope wants to observe at.
'''


@dataclass
class Reservation:
    facility: Facility
    time: TimeWindow
    frequency: FrequencyRange = field(default_factory=FrequencyRange)

    def __str__(self):
        return (
            f'{self.__class__.__name__}:\n'
            f'{self.facility}\n'
            f'{self.time}\n'
            f'{self.frequency}'
        )
