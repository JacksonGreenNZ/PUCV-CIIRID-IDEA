from dataclasses import dataclass, field
from typing import List, Optional

from sopp.custom_dataclasses.observation_target import ObservationTarget
from sopp.custom_dataclasses.position import Position
from sopp.custom_dataclasses.position_time import PositionTime
from sopp.custom_dataclasses.reservation import Reservation
from sopp.custom_dataclasses.runtime_settings import RuntimeSettings


@dataclass
class ConfigurationFile:
    reservation: Reservation
    runtime_settings: RuntimeSettings = field(default_factory=RuntimeSettings)
    antenna_position_times: Optional[List[PositionTime]] = None
    observation_target: Optional[ObservationTarget] = None
    static_antenna_position: Optional[Position] = None
