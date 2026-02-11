import json
import os
from contextlib import contextmanager
from datetime import datetime, timezone
from io import TextIOWrapper
from pathlib import Path
from typing import ContextManager, List, Optional, Union
from uuid import uuid4

from dateutil import parser


def read_json_file(filepath: Path) -> dict:
    with open(filepath, 'r') as f:
        return json.load(f)


@contextmanager
def temporary_file(filepath: Optional[Path] = None) -> ContextManager[TextIOWrapper]:
    filepath = Path(filepath or f'{uuid4().hex}.tmp')
    with open(filepath, 'w') as f:
        yield f
    filepath.unlink(missing_ok=True)


def convert_datetime_to_utc(localtime: datetime) -> datetime:
    if localtime.tzinfo == timezone.utc:
        return localtime
    elif localtime.tzinfo is None:
        return localtime.replace(tzinfo=timezone.utc)
    else:
        return localtime.astimezone(timezone.utc)


def read_datetime_string_as_utc(string_value: str) -> datetime:
    try:
        time = parser.parse(string_value)
        return convert_datetime_to_utc(time)
    except ValueError:
        raise ValueError(f"Unable to parse datetime string: {string_value}")


def parse_time_and_convert_to_utc(time: Union[str, datetime]) -> datetime:
    try:
        return read_datetime_string_as_utc(time)
    except TypeError:
        return convert_datetime_to_utc(time)


def get_script_directory(module) -> Path:
    return Path(os.path.dirname(os.path.realpath(module)))


SUPPLEMENTS_DIRECTORY_NAME = 'supplements'
def get_supplements_directory() -> Path:
    return Path(get_script_directory(__file__), '..', SUPPLEMENTS_DIRECTORY_NAME)


SATELLITES_FILENAME = 'satellites.tle'
def get_satellites_filepath() -> Path:
    return Path(get_supplements_directory(), SATELLITES_FILENAME)


FREQUENCIES_FILENAME = 'satellite_frequencies.csv'
def get_frequencies_filepath() -> Path:
    return Path(get_supplements_directory(), FREQUENCIES_FILENAME)


CONFIG_FILE_FILENAME = '.config'
CONFIG_FILE_FILENAME_JSON = 'config.json'
def default_config_filepaths() -> List[Path]:
    return [Path(get_supplements_directory(), CONFIG_FILE_FILENAME), Path(get_supplements_directory(), CONFIG_FILE_FILENAME_JSON)]


def get_default_config_file_filepath() -> Optional[Path]:
    return next((path for path in default_config_filepaths() if path.exists()), None)
