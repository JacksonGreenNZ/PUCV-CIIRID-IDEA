import numpy as np
from skyfield.api import load, wgs84, Star
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
                 ra_hours: float, dec_degrees: float, time_begin: str, time_end: str):
        self.ts = load.timescale()
        self.planets = load('de421.bsp')
        self.earth = self.planets['earth']
        self.location = wgs84.latlon(latitude, longitude, elevation_m=elevation_m)
        self.observer = self.location + self.earth
        self.target = Star(ra_hours=ra_hours, dec_degrees=dec_degrees)
        self._time_begin = time_begin
        self._time_end = time_end
        self._precompute_target_positions()

    def _precompute_target_positions(self):
        """
        vectorised computation of target alt/az across full observation window at 1 second steps for later angular separation comparisons
        """
        t_begin = self._time_begin
        t_end   = self._time_end

        one_second = 1 / 86400.0
        self._time_array = self.ts.tt_jd(
            np.arange(t_begin.tt, t_end.tt, one_second)
        )

        apparent = self.observer.at(self._time_array).observe(self.target).apparent()
        alt, az, _ = apparent.altaz()

        self._target_alts = alt.degrees
        self._target_azs  = az.degrees
        
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