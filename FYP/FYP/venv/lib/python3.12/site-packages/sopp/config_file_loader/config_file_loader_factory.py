from pathlib import Path
from typing import Optional

from sopp.config_file_loader.support.config_file_loader_base import ConfigFileLoaderBase
from sopp.config_file_loader.support.config_file_loader_json import ConfigFileLoaderJson
from sopp.utilities import get_default_config_file_filepath


def get_config_file_object(config_filepath: Optional[Path] = None) -> ConfigFileLoaderBase:
    config_filepath = config_filepath or get_default_config_file_filepath()
    for config_class in [ConfigFileLoaderJson]:
        if config_class.filename_extension() in str(config_filepath):
            return config_class(filepath=config_filepath)
