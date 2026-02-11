from datetime import datetime, timedelta
from math import ceil
from typing import List

from sopp.custom_dataclasses.time_window import TimeWindow


class EvenlySpacedTimeIntervalsCalculator:
    def __init__(self, time_window: TimeWindow, resolution: timedelta = timedelta(seconds=1)):
        self._resolution = resolution
        self._time_window = time_window

    def run(self) -> List[datetime]:
        timespan = self._time_window.end - self._time_window.begin
        return [self._time_window.begin + self._resolution * i for i in range(ceil(timespan / self._resolution))]
