from dataclasses import dataclass
from datetime import datetime

from sopp.custom_dataclasses.position import Position


@dataclass
class PositionTime:
    position: Position
    time: datetime
