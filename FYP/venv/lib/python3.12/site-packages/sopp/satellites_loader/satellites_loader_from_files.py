from dataclasses import replace
from typing import List
from functools import cached_property

from sopp.satellites_loader.satellites_loader import SatellitesLoader
from sopp.custom_dataclasses.satellite.satellite import Satellite
from sopp.custom_dataclasses.frequency_range.support.get_frequency_data_from_csv import \
    GetFrequencyDataFromCsv


class SatellitesLoaderFromFiles(SatellitesLoader):
    """
    A class for loading satellite information from TLE (Two-Line Element) and a frequency data file.

    This class extends the `SatellitesLoader` class to provide functionality for loading satellite
    information from TLE files and optionally associating frequency data with the satellites.

    Example usage:

    >>> loader = SatellitesLoaderFromFiles(tle_file='satellite_data.tle', frequency_file='frequency_data.csv')
    >>> satellites = loader.load_satellites()
    >>> for satellite in satellites:
    >>>     print(satellite)
    """

    def __init__(self, tle_file, frequency_file=None):
        self.tle_file = tle_file
        self.frequency_file = frequency_file

    def load_satellites(self) -> List[Satellite]:
        return self._populate_satellites_with_frequency_data() if self._satellites_freq_data else self._satellites_from_tle

    def _populate_satellites_with_frequency_data(self):
        return [
            replace(
                satellite,
                frequency=self._satellites_freq_data.get(satellite.tle_information.satellite_number, [])
            )
            for satellite in self._satellites_from_tle
        ]

    @cached_property
    def _satellites_from_tle(self):
        return Satellite.from_tle_file(tlefilepath=self.tle_file)

    @cached_property
    def _satellites_freq_data(self):
        return self.frequency_file and GetFrequencyDataFromCsv(filepath=self.frequency_file).get()
