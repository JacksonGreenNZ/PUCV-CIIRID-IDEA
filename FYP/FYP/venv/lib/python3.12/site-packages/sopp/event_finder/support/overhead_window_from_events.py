from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List
from sopp.custom_dataclasses.overhead_window import OverheadWindow
from sopp.custom_dataclasses.reservation import Reservation
from sopp.custom_dataclasses.satellite.satellite import Satellite
from sopp.custom_dataclasses.time_window import TimeWindow


class EventTypesRhodesmill(Enum):
    """
    Skyfield API returns events as 0, 1, or 2 for enters, culminates, exits, respectively
    """
    ENTERS = 0
    CULMINATES = 1
    EXITS = 2


@dataclass
class EventRhodesmill:
    event_type: EventTypesRhodesmill
    satellite: Satellite
    timestamp: datetime


class OverheadWindowFromEvents:
    def __init__(self, events: List[EventRhodesmill], reservation: Reservation):
        self._events = events
        self._reservation = reservation

    def get(self) -> List[OverheadWindow]:
        enter_events, culminate_events, exit_events = ([event for event in self._events if event.event_type == event_type]
                                     for event_type in EventTypesRhodesmill)

        if (len(self._events) == 1) and (self._events[0].event_type == EventTypesRhodesmill.CULMINATES): #handles sat that is in view for entire reservation
            time_window = TimeWindow(begin=self._reservation.time.begin, end=self._reservation.time.end)
            overhead_windows = [OverheadWindow(satellite=self._events[0].satellite, overhead_time=time_window)]
        else:
            if len(enter_events) != len(exit_events): #Handle case where a satellite starts xor ends in observation area
                if self._events[0].event_type == EventTypesRhodesmill.ENTERS: #the first event is the satellite entering view, so it didn't start in observation area
                    end_reservation_event = EventRhodesmill(event_type=EventTypesRhodesmill.EXITS, satellite=self._events[0].satellite, timestamp=self._reservation.time.end)
                    exit_events.append(end_reservation_event)
                elif self._events[0].event_type == EventTypesRhodesmill.EXITS or self._events[0].event_type == EventTypesRhodesmill.CULMINATES: #the first event is an exit, so the sat starts in view
                    start_reservation_event = EventRhodesmill(event_type=EventTypesRhodesmill.ENTERS, satellite=self._events[0].satellite, timestamp=self._reservation.time.begin)
                    enter_events.insert(0, start_reservation_event)
            elif len(enter_events) == len(exit_events) and self._events[0].event_type != EventTypesRhodesmill.ENTERS:
                start_reservation_event = EventRhodesmill(event_type=EventTypesRhodesmill.ENTERS, satellite=self._events[0].satellite, timestamp=self._reservation.time.begin)
                enter_events.insert(0, start_reservation_event)
                end_reservation_event = EventRhodesmill(event_type=EventTypesRhodesmill.EXITS, satellite=self._events[0].satellite, timestamp=self._reservation.time.end)
                exit_events.append(end_reservation_event)
            enter_and_exit_pairs = zip(enter_events, exit_events)
            time_windows = [TimeWindow(begin=begin_event.timestamp, end=exit_event.timestamp) for begin_event, exit_event in enter_and_exit_pairs]
            overhead_windows = [OverheadWindow(satellite=self._events[0].satellite, overhead_time=time_window) for time_window in time_windows]
        return overhead_windows
