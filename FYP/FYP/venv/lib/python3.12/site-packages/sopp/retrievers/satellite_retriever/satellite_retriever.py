from typing import List

from sopp.custom_dataclasses.satellite.satellite import Satellite
from sopp.retrievers.retriever import Retriever


class SatelliteRetriever(Retriever):
    def retrieve(self) -> List[Satellite]:
        pass
