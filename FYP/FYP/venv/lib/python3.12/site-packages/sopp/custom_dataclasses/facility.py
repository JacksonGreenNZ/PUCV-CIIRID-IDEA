from dataclasses import dataclass, field
from sopp.custom_dataclasses.coordinates import Coordinates
from typing import List, Optional

from sopp.custom_dataclasses.position_time import PositionTime


@dataclass
class Facility:
    '''
    The Facility data class contains the observation parameters of the facility and the object it is tracking, including coordinates
    of the RA telescope and its beamwidth, as well as the right ascension and declination values for its observation target:

    -coordinates:       location of RA facility. Coordinates.
    -beamwidth:         beamwidth of the telescope. float. Defaults to 3
    -elevation:         ground elevation of the telescope in meters. float. Defaults to 0
    -name:              name of the facility. String. Defaults to 'Unnamed Facility'
    '''
    coordinates: Coordinates
    beamwidth: float = 3
    elevation: float = 0
    name: Optional[str] = 'Unnamed Facility'

    @property
    def half_beamwidth(self) -> float:
        return self.beamwidth / 2

    def __str__(self):
        return (
            f'{self.__class__.__name__}:\n'
            f'  Name:               {self.name}\n'
            f'  Latitude:           {self.coordinates.latitude}\n'
            f'  Longitude:          {self.coordinates.longitude}\n'
            f'  Elevation:          {self.elevation} meters\n'
            f'  Beamwidth:          {self.beamwidth} degrees'
        )
