import json
import zlib
from uuid import uuid4
from datetime import datetime, timezone
from typing import Optional, List, Dict
from functools import cached_property

from sopp.custom_dataclasses.reservation import Reservation


class Tardys4Generator:
    """
    A class that generates a spectrum reservation for the TARDYs4 specification.

    Parameters:
    - reservation: The Reservation object used during satellite interference
      detection.
    - begin: The elected begin time for the actual observation.
    - end: The elected end time for the actual observation.
    - dpa_id: Optional DPAID for reservation.
    - location_radius: The protection radius in km. Defaults to 1.
    """

    def __init__(
        self,
        reservation: Reservation,
        begin: datetime,
        end: datetime,
        dpa_id: Optional[str] = None,
        location_radius: float = 1
    ):
        self._reservation: Reservation = reservation
        self._begin: datetime = begin
        self._end: datetime = end
        self._loc_radius: float = location_radius
        self._loc_lat: float = reservation.facility.coordinates.latitude
        self._loc_long: float = reservation.facility.coordinates.longitude
        self._elevation: float = reservation.facility.elevation
        self._region_size: int = reservation.facility.beamwidth
        self._dpa_id: Optional[str] = dpa_id

    def write_to_file(self, filename: str = "tardys4_reservation.json"):
        with open(filename, "w") as f:
            json.dump(self.tardys4, f)

    @cached_property
    def tardys4(self) -> Dict[str, any]:
        return {
            "transactionId": self._transaction_id,
            "dateTimePublished": self._time,
            "dateTimeCreated": self._time,
            "checksum": self._checksum,
            "scheduledEvents": self._scheduled_events,
        }

    @property
    def _scheduled_events(self) -> List[Dict[str, any]]:
        return [
            {
                "eventId": self._event_id,
                "dpaId": self._dpa_id,
                "locLat": self._loc_lat,
                "locLong": self._loc_long,
                "locRadius": self._loc_radius,
                "locElevation": self._elevation,
                "coordType": "azel",
                "eventStatus": "actual",
                "dateTimeStart": self._begin_utc,
                "dateTimeEnd": self._end_utc,
                "freqStart": self._freq_start_hz,
                "freqStop": self._freq_end_hz,
                "regionSize": self._region_size,
                "regionX": 90,
                "regionY": 45,
            },
        ]

    @property
    def _begin_utc(self) -> str:
        return self._begin.astimezone(timezone.utc).isoformat()

    @property
    def _end_utc(self) -> str:
        return self._end.astimezone(timezone.utc).isoformat()

    @property
    def _freq_start_hz(self) -> int:
        return int(self._reservation.frequency.low_mhz * 10**6)

    @property
    def _freq_end_hz(self) -> int:
        return int(self._reservation.frequency.high_mhz * 10**6)

    @cached_property
    def _time(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    @cached_property
    def _transaction_id(self) -> str:
        return str(uuid4())

    @cached_property
    def _event_id(self) -> str:
        return str(uuid4())

    @property
    def _checksum(self) -> str:
        return format(zlib.crc32(json.dumps(self._scheduled_events).encode()), "x")
