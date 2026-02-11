from abc import ABC, abstractmethod
from typing import List

from sopp.custom_dataclasses.satellite.satellite import Satellite


class SatellitesLoader(ABC):
    @abstractmethod
    def load_satellites(self) -> List[Satellite]:
        pass
