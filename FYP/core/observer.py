import numpy as np
from skyfield.api import load, wgs84, Star
from datetime import datetime, timezone
from config import (
    LATITUDE, LONGITUDE, ELEVATION_M,
    RA_HOURS, DEC_DEGREES,
    TIME_BEGIN, TIME_END
)
from datetime import datetime, timezone

class Observer:
    """
    Wraps skyfield setup, precomputes target positions across observation window,
    and provides angular separation via haversine.
    """
    def __init__(self, latitude: float, longitude: float, elevation_m: float,
                 time_begin: str, time_end: str,
                 ra_hours: float | None = None, dec_degrees: float | None = None,
                 azimuth_deg: float | None = None, altitude_deg: float | None = None):
        self.ts = load.timescale()
        self.planets = load('de421.bsp')
        self.earth = self.planets['earth']
        self.location = wgs84.latlon(latitude, longitude, elevation_m=elevation_m)
        self.observer = self.location + self.earth
        self._time_begin = time_begin
        self._time_end = time_end
        self._is_static = azimuth_deg is not None and altitude_deg is not None
        self._fixed_az = azimuth_deg
        self._fixed_alt = altitude_deg

        if not self._is_static:
            assert ra_hours is not None and dec_degrees is not None
            self.target = Star(ra_hours=ra_hours, dec_degrees=dec_degrees)

        self._precompute_target_positions()

    def _precompute_target_positions(self):
        t_begin = self.ts.utc(
            datetime.fromisoformat(self._time_begin).replace(tzinfo=timezone.utc)
        )
        t_end = self.ts.utc(
            datetime.fromisoformat(self._time_end).replace(tzinfo=timezone.utc)
        )
        one_second = 1 / 86400.0
        self._time_array = self.ts.tt_jd(
            np.arange(t_begin.tt, t_end.tt, one_second)
        )

        if self._is_static:
            # fixed pointing — same az/alt for every timestep
            n = len(self._time_array.tt)
            self._target_alts = np.full(n, self._fixed_alt)
            self._target_azs = np.full(n, self._fixed_az)
        else:
            apparent = self.observer.at(self._time_array).observe(self.target).apparent()
            alt, az, _ = apparent.altaz()
            self._target_alts = alt.degrees
            self._target_azs = az.degrees
        
    #public properties for visualisation 
    @property
    def target_alts(self):
        """Full precomputed target altitude array in degrees."""
        return self._target_alts
    @property
    def target_azs(self):
        """Full precomputed target azimuth array in degrees."""
        return self._target_azs
    @property
    def time_array(self):
        """Full precomputed time array as skyfield time object."""
        return self._time_array

    def get_target_position(self, sat_time):
        """
        returns precomputed target (alt, az) in degrees closest to the given SOPP timestamp.

        :param sat_time: SOPP position time object
        """
        t = self.ts.utc(
            sat_time.year, sat_time.month, sat_time.day,
            sat_time.hour, sat_time.minute,
            sat_time.second + sat_time.microsecond * 1e-6
        )
        idx = np.argmin(np.abs(self._time_array.tt - t.tt))
        return self._target_alts[idx], self._target_azs[idx]

    def angular_separation(self, alt1, az1, alt2, az2):
        """
        Haversine angular separation between two alt/az positions.
        All inputs in degrees, returns degrees.

        :param alt1: altitude of first point
        :param az1: azimuth of first point
        :param alt2: altitude of second point
        :param az2: azimuth of second point
        """
        alt1, az1, alt2, az2 = map(np.radians, [alt1, az1, alt2, az2])
        d_az = az2 - az1
        cos_sep = (np.sin(alt1) * np.sin(alt2) + np.cos(alt1) * np.cos(alt2) * np.cos(d_az))
        return np.degrees(np.arccos(np.clip(cos_sep, -1, 1)))