import json
from functools import cached_property
from typing import List

from sopp.config_file_loader.support.config_file_loader_base import ConfigFileLoaderBase
from sopp.custom_dataclasses.configuration_file import ConfigurationFile
from sopp.custom_dataclasses.coordinates import Coordinates
from sopp.custom_dataclasses.facility import Facility
from sopp.custom_dataclasses.frequency_range.frequency_range import FrequencyRange
from sopp.custom_dataclasses.observation_target import ObservationTarget
from sopp.custom_dataclasses.position import Position
from sopp.custom_dataclasses.position_time import PositionTime
from sopp.custom_dataclasses.reservation import Reservation
from sopp.custom_dataclasses.time_window import TimeWindow
from sopp.custom_dataclasses.runtime_settings import RuntimeSettings
from sopp.utilities import read_datetime_string_as_utc


class ConfigFileLoaderJson(ConfigFileLoaderBase):
    @cached_property
    def configuration(self) -> ConfigurationFile:
        return ConfigurationFile(
            reservation=self._reservation,
            runtime_settings=self._runtime_settings,
            antenna_position_times=self._antenna_position_times,
            observation_target=self._observation_target,
            static_antenna_position=self._static_antenna_position
        )

    @cached_property
    def _reservation(self) -> Reservation:
        return Reservation(
            facility=self._facility,
            time=self._reservation_window,
            frequency=self._frequency_range
        )

    @cached_property
    def _facility(self) -> Facility:
        configuration = self._config_object.get('facility')

        return Facility(
                coordinates=Coordinates(
                    latitude=configuration['latitude'],
                    longitude=configuration['longitude']
                ),
                name=configuration['name'],
                elevation=configuration['elevation'],
        )

    @cached_property
    def _reservation_window(self) -> TimeWindow:
        configuration = self._config_object.get('reservationWindow')
        start_datetime = read_datetime_string_as_utc(configuration['startTimeUtc'])
        end_datetime_str = read_datetime_string_as_utc(configuration['endTimeUtc'])

        return TimeWindow(begin=start_datetime, end=end_datetime_str)

    @cached_property
    def _frequency_range(self) -> FrequencyRange:
        configuration = self._config_object.get('frequencyRange')

        return FrequencyRange(
            frequency=configuration['frequency'],
            bandwidth=configuration['bandwidth']
        )

    @cached_property
    def _runtime_settings(self) -> RuntimeSettings:
        configuration = self._config_object.get('runtimeSettings')

        return RuntimeSettings(
            time_continuity_resolution=configuration['time_continuity_resolution'],
            concurrency_level=configuration['concurrency_level']
        ) if configuration else RuntimeSettings()

    @cached_property
    def _antenna_position_times(self) -> List[PositionTime]:
        configuration = self._config_object.get('antennaPositionTimes')
        return configuration and [PositionTime(position=Position(altitude=position_time['altitude'],
                                                                 azimuth=position_time['azimuth']),
                                               time=read_datetime_string_as_utc(string_value=position_time['time']))
                                  for position_time in configuration]

    @cached_property
    def _observation_target(self) -> ObservationTarget:
        configuration = self._config_object.get('observationTarget')
        return configuration and ObservationTarget(
            declination=configuration['declination'],
            right_ascension=configuration['rightAscension']
        )

    @cached_property
    def _static_antenna_position(self) -> Position:
        configuration = self._config_object.get('staticAntennaPosition')
        return configuration and Position(
            altitude=configuration['altitude'],
            azimuth=configuration['azimuth']
        )

    @cached_property
    def _config_object(self) -> dict:
        with open(self._filepath, 'r') as f:
            return json.load(f)

    @classmethod
    def filename_extension(cls) -> str:
        return '.json'
