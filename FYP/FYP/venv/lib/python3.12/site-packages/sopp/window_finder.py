from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List

from sopp.custom_dataclasses.frequency_range.frequency_range import FrequencyRange
from sopp.custom_dataclasses.overhead_window import OverheadWindow
from sopp.custom_dataclasses.position_time import PositionTime
from sopp.custom_dataclasses.reservation import Reservation
from sopp.custom_dataclasses.satellite.satellite import Satellite
from sopp.custom_dataclasses.time_window import TimeWindow
from sopp.event_finder.event_finder_rhodesmill.event_finder_rhodesmill import EventFinderRhodesmill


@dataclass
class SuggestedReservation:
    ideal_reservation: Reservation
    overhead_satellites: List[OverheadWindow]
    suggested_start_time: datetime


class WindowFinder:
    def __init__(self,
                 ideal_reservation: Reservation,
                 satellites: List[Satellite],
                 search_window: timedelta = timedelta(days=1),
                 start_time_increments: timedelta = timedelta(minutes=120)):
        self._ideal_reservation = ideal_reservation
        self._satellites = satellites
        self._search_window = search_window
        self._start_time_increments = start_time_increments

    def search(self) -> List[SuggestedReservation]:
        suggested_reservations = []
        search_start_time = self._ideal_reservation.time.begin - (self._search_window/2)
        search_end_time = self._ideal_reservation.time.begin + (self._search_window/2)
        search_window_res = Reservation(facility=self._ideal_reservation.facility, time=TimeWindow(begin=search_start_time, end=search_end_time), frequency=self._ideal_reservation.frequency)
        overhead_satellites = self._satellites_overhead(search_window_res)
        potential_time_windows = [TimeWindow(begin=start_time, end=start_time + self._ideal_reservation.time.duration)
                                  for start_time in self._potential_start_times]
        for reservation_window in potential_time_windows:
            overhead_satellites_res = []
            for interference_window in overhead_satellites:
                if (reservation_window.begin <= interference_window.overhead_time.begin <= reservation_window.end) or \
                        (reservation_window.begin <= interference_window.overhead_time.end <= reservation_window.end) or \
                        (interference_window.overhead_time.begin <= reservation_window.begin) and (interference_window.overhead_time.end >= reservation_window.end):
                    overhead_satellites_res.append(interference_window)
            suggested_reservations.append(
                SuggestedReservation(
                    ideal_reservation=self._ideal_reservation,
                    overhead_satellites=overhead_satellites_res,
                    suggested_start_time=reservation_window.begin
                )
            )
        suggested_reservations.sort(key=lambda x: len(x.overhead_satellites))
        return suggested_reservations

    def find(self) -> List[SuggestedReservation]:
        potential_time_windows = [TimeWindow(begin=start_time, end=start_time + self._ideal_reservation.time.duration)
                                  for start_time in self._potential_start_times]
        potential_reservations = [Reservation(facility=self._ideal_reservation.facility, time=time, frequency=FrequencyRange(frequency=None, bandwidth=None)) for time in potential_time_windows]
        overhead_satellites = [self._satellites_overhead(reservation=reservation) for reservation in potential_reservations]
        sort_indices = sorted(range(len(potential_reservations)), key=lambda index: len(overhead_satellites[index]))
        return [
            SuggestedReservation(
                ideal_reservation=self._ideal_reservation,
                overhead_satellites=overhead_satellites[index],
                suggested_start_time=potential_reservations[index].time.begin
            )
            for index in sort_indices
        ]

    def _satellites_overhead(self, reservation: Reservation) -> List[OverheadWindow]:
        return EventFinderRhodesmill(list_of_satellites=self._satellites,
                                     reservation=reservation,
                                     antenna_direction_path=[PositionTime(altitude=0, azimuth=0, time=reservation.time.begin)]).get_satellites_above_horizon()

    @property
    def _potential_start_times(self) -> List[datetime]:
        number_of_slots = int(self._search_window.total_seconds() / self._start_time_increments.total_seconds())
        return [self._get_time_slot(i) for i in range(1, number_of_slots + 1)]

    def _get_time_slot(self, index: int) -> datetime:
        backwards_forwards = (-1) ** index
        multiplier = int(index / 2)
        return self._ideal_reservation.time.begin + backwards_forwards * self._start_time_increments * multiplier
