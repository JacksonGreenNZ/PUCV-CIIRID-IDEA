from dataclasses import dataclass, field
from datetime import timedelta

'''
The RuntimeSettings class stores the run time settings used in EventFinderRhodesMill
  + time_continutity_resolution: The time step resolution used to calculate satellite positions. (Default 1 second)
  + concurrency_level: The number of cores to use for multiprocessing the satellite position calculations. (Default 2)
  + min_altitude: The minimum altitude that a satellite must be to be considered above horizon. (Default 0.0)
'''


@dataclass
class RuntimeSettings:
    time_continuity_resolution: timedelta = field(default=timedelta(seconds=1))
    concurrency_level: int = field(default=1)
    min_altitude: float = field(default=0.0)

    def __post_init__(self):
        if isinstance(self.time_continuity_resolution, int):
            self.time_continuity_resolution = timedelta(seconds=self.time_continuity_resolution)

    def __str__(self):
        return (
            f'{self.__class__.__name__}:\n'
            f'  Time Interval:      {self.time_continuity_resolution}\n'
            f'  Concurrency:        {self.concurrency_level}'
            f'  Min. Altitude:      {self.min_altitude}'
        )
