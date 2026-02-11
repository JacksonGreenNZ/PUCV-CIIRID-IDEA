from abc import ABC
from pathlib import Path

from sopp.retrievers.retriever import Retriever
from sopp.utilities import read_json_file


class RetrieverJsonFile(Retriever, ABC):
    def __init__(self, filepath: Path):
        self._filepath = filepath

    @property
    def _json(self) -> dict:
        return read_json_file(filepath=self._filepath)
