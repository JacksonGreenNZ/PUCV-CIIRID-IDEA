from dataclasses import dataclass


@dataclass
class ObservationTarget:
    declination: str
    right_ascension: str
