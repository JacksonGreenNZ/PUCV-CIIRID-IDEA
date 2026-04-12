import sys
import shutil
import numpy as np
from skyfield.api import Loader, wgs84, Star
from datetime import datetime, timezone
from pathlib import Path
from core.paths import get_base_dir, is_frozen

def _seed_ephemeris():
    """Copy de421.bsp from the PyInstaller bundle to the user data dir if not present."""
    dest = get_base_dir() / "de421.bsp"
    if not dest.exists() and is_frozen():
        bundled = Path(getattr(sys, "_MEIPASS", "")) / "de421.bsp"
        if bundled.exists():
            shutil.copy2(bundled, dest)

_seed_ephemeris()
load = Loader(get_base_dir())

class Observer:
    """
    Wraps skyfield setup, precomputes target positions across observation window,
    and provides angular separation via haversine.

    On construction, the full observation window is sampled at 1-second
    resolution and target alt/az positions are stored as numpy arrays for fast
    lookup during interference checking. Supply either RA/Dec (tracking target)
    or Az/Alt (fixed pointing), not both.

    :param latitude: Observatory latitude in decimal degrees (positive = North).
    :param longitude: Observatory longitude in decimal degrees (positive = East).
    :param elevation_m: Observatory elevation above sea level in metres.
    :param time_begin: ISO 8601 UTC start of the observation window.
    :param time_end: ISO 8601 UTC end of the observation window.
    :param ra_hours: Right ascension of the tracking target in hours.
    :param dec_degrees: Declination of the tracking target in degrees.
    :param azimuth_deg: Fixed azimuth for static pointings in degrees.
    :param altitude_deg: Fixed altitude for static pointings in degrees.
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

    def get_target_position(self, sat_time) -> tuple[float, float]:
        """
        Return the precomputed target (alt, az) in degrees nearest to a SOPP event timestamp.

        Finds the closest index in the precomputed time array using argmin on
        the difference in Terrestrial Time (TT), then returns the corresponding
        altitude and azimuth from the precomputed arrays.

        :param sat_time: SOPP position time object with year/month/day/hour/minute/second/microsecond.
        :returns: Tuple of (altitude_deg, azimuth_deg).
        """
        t = self.ts.utc(
            sat_time.year, sat_time.month, sat_time.day,
            sat_time.hour, sat_time.minute,
            sat_time.second + sat_time.microsecond * 1e-6
        )
        idx = np.argmin(np.abs(self._time_array.tt - t.tt))
        return self._target_alts[idx], self._target_azs[idx]

    @staticmethod
    def angular_separation(alt1, az1, alt2, az2):
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