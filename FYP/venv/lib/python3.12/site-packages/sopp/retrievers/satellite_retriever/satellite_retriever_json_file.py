from typing import List

from sopp.custom_dataclasses.satellite.satellite import Satellite
from sopp.retrievers.retriever_json_file import RetrieverJsonFile
from sopp.retrievers.satellite_retriever.satellite_retriever import SatelliteRetriever

SATELLITES_JSON_KEY = 'satellites'


class SatelliteRetrieverJsonFile(SatelliteRetriever, RetrieverJsonFile):
    def retrieve(self) -> List[Satellite]:
        return [Satellite.from_json(info) for info in self._json[SATELLITES_JSON_KEY]]
