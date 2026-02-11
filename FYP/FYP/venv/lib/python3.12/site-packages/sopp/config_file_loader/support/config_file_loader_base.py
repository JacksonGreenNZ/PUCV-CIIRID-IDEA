from abc import ABC, abstractmethod
from functools import cached_property
from pathlib import Path

from sopp.custom_dataclasses.configuration_file import ConfigurationFile


class ConfigFileLoaderBase(ABC):
    def __init__(self, filepath: Path):
        self._filepath = filepath

    @cached_property
    @abstractmethod
    def configuration(self) -> ConfigurationFile:
        pass

    @classmethod
    @abstractmethod
    def filename_extension(cls) -> str:
        pass
