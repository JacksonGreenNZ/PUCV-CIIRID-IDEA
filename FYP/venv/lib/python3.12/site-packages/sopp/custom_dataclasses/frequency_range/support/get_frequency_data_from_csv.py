import csv
from enum import Enum
from pathlib import Path
from typing import Dict, List
from collections import defaultdict

from sopp.custom_dataclasses.frequency_range.frequency_range import FrequencyRange


class FrequencyCsvKeys(Enum):
    LINENO = ''
    ID = 'ID'
    NAME = 'Name'
    FREQUENCY = 'Frequency [MHz]'
    BANDWIDTH = 'Bandwidth [kHz]/Baud'
    STATUS = 'Status'
    DESCRIPTION = 'Description'
    SOURCE = 'Source'


class GetFrequencyDataFromCsv:
    '''
    Reads frequency data from a supplied CSV. The CSV should be placed in the `supplements` folder under the name `satellite_frequencies.csv` and should be
    formatted with the following columns:
    ________________________________________________________________________________________________________
    | LineNo |   ID   |   Name   |   Frequency   |   Bandwidth   |   Status   |   Description   |  Source  |

    With all values in the frequency column of the same order of magnitude (typically MHz). The same goes for bandwidth. These columns should have the integer value alone.


    '''
    def __init__(self, filepath: Path):
        self._filepath = filepath

    def get(self) -> Dict[int, List['FrequencyRange']]:
        frequencies = defaultdict(list)
        for line in self._data[1:]:
            id_string = line[FrequencyCsvKeys.ID.value]
            if not id_string or id_string == 'None' or id_string == "nan":
                continue

            frequency_range = FrequencyRange(frequency=self._get_frequency(line),
                                             bandwidth=self._get_bandwidth(line),
                                             status=self._get_status(line))
            id_int = int(id_string)
            frequencies[id_int].append(frequency_range)

        return frequencies

    def _get_frequency(self, line: Dict[str, str]):
        frequency = line[FrequencyCsvKeys.FREQUENCY.value]
        try:
            return float(frequency)
        except (TypeError, ValueError):
            return None

    def _get_bandwidth(self, line: Dict[str, str]):
        bandwidth = line[FrequencyCsvKeys.BANDWIDTH.value]
        try:
            bandwidth = float(bandwidth.split()[0])
            return self._convert_khz_to_mhz(bandwidth)
        except (TypeError, ValueError, IndexError):
            return None

    def _get_status(self, line: Dict[str, str]):
        status = line[FrequencyCsvKeys.STATUS.value].lower()
        return status

    def _convert_khz_to_mhz(self, khz: float):
        return khz / 1000

    @property
    def _data(self) -> List[Dict[str, str]]:
        with open(self._filepath, 'r') as file:
            return list(csv.DictReader(file, fieldnames=[e.value for e in FrequencyCsvKeys]))
