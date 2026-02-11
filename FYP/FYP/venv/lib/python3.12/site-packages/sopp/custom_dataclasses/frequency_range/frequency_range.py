from dataclasses import dataclass
from typing import Optional

'''
The FrequencyRange class is used for storing frequency ranges of both the RA telescopes observation and each satellite's downlink transmission
frequency information. The frequency parameter represents the center frequency of the observation or downlink. The status parameter is only relevant
to satellites and is used to store information from the satellite frequency database on whether an antenna is operational 'active' or not 'inactive'

The overlaps function determines if two FrequencyRanges overlap with each other and is used to determine if any of the satellite downlink frequencies
overlap with the observation frequency. Satellite frequency data is read from a csv file (as of May 15, 2023) using the GetFrequencyDataFromCsv class
under the support folder.f

'''

DEFAULT_BANDWIDTH = 10

@dataclass
class FrequencyRange:
    frequency: Optional[float] = None
    bandwidth: Optional[float] = None
    status: Optional[str] = None

    @property
    def low_mhz(self):
        return self.frequency - self._half_bandwidth

    @property
    def high_mhz(self):
        return self.frequency + self._half_bandwidth

    @property
    def _half_bandwidth(self):
        return self.bandwidth / 2

    def overlaps(self, satellite_frequency: 'FrequencyRange'):
        half_bandwidth_sat = DEFAULT_BANDWIDTH / 2 if satellite_frequency.bandwidth is None else satellite_frequency.bandwidth
        low_mhz_sat = satellite_frequency.frequency - half_bandwidth_sat
        high_mhz_sat = satellite_frequency.frequency + half_bandwidth_sat

        return low_mhz_sat < self.high_mhz and high_mhz_sat > self.low_mhz

    def __str__(self):
        return (
            f'{self.__class__.__name__}:\n'
            f'  Frequency:          {self.frequency} MHz\n'
            f'  Bandwidth:          {self.bandwidth} MHz'
        )
