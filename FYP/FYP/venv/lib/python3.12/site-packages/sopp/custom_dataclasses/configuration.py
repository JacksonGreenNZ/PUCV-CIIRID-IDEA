from dataclasses import dataclass, field
from typing import List, Optional

from sopp.custom_dataclasses.observation_target import ObservationTarget
from sopp.custom_dataclasses.position import Position
from sopp.custom_dataclasses.position_time import PositionTime
from sopp.custom_dataclasses.reservation import Reservation
from sopp.custom_dataclasses.runtime_settings import RuntimeSettings
from sopp.custom_dataclasses.satellite.satellite import Satellite


@dataclass
class Configuration:
    reservation: Reservation
    satellites: List[Satellite]
    antenna_direction_path: List[PositionTime]
    runtime_settings: RuntimeSettings = field(default_factory=RuntimeSettings)

    def __str__(self):
        return (
            f'{self.__class__.__name__}:\n'
            f'{self.reservation}\n'
            f'{self.runtime_settings}\n'
            f'Satellites:           {len(self.satellites)} total'
        )
