from datetime import datetime
from typing import List

from skyfield.api import load
from skyfield.toposlib import wgs84

from sopp.event_finder.event_finder_rhodesmill.support.satellite_positions_with_respect_to_facility_retriever.satellite_positions_with_respect_to_facility_retriever import \
    SatellitePositionsWithRespectToFacilityRetriever
from sopp.custom_dataclasses.position import Position
from sopp.custom_dataclasses.position_time import PositionTime
from sopp.custom_dataclasses.facility import Facility
from sopp.custom_dataclasses.satellite.satellite import Satellite


RHODESMILL_TIMESCALE = load.timescale()


class SatellitePositionsWithRespectToFacilityRetrieverRhodesmill(SatellitePositionsWithRespectToFacilityRetriever):
    def __init__(self, facility: Facility, datetimes: List[datetime]):
        super().__init__(facility, datetimes)
        self._timescales = RHODESMILL_TIMESCALE.from_datetimes(datetimes)
        self._facility_latlon = self._calculate_facility_latlon()

    def run(self, satellite: Satellite) -> List[PositionTime]:
        satellite_rhodesmill_with_respect_to_facility = satellite.to_rhodesmill() - self._facility_latlon

        topocentric = satellite_rhodesmill_with_respect_to_facility.at(self._timescales)
        altitude, azimuth, distance = topocentric.altaz()

        return [
            PositionTime(
                Position(altitude=altitude, azimuth=azimuth, distance_km=distance_km),
                time=time
            )
            for altitude, azimuth, distance_km, time in zip(altitude.degrees, azimuth.degrees, distance.km, self._datetimes)
        ]

    def _calculate_facility_latlon(self):
        return wgs84.latlon(
            latitude_degrees=self._facility.coordinates.latitude,
            longitude_degrees=self._facility.coordinates.longitude,
            elevation_m=self._facility.elevation
        )
