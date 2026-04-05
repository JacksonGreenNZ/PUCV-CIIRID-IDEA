import os
from dataclasses import dataclass, field

@dataclass
class RunConfig:
    latitude: float
    longitude: float
    elevation_m: float
    dish_diameter_m: float
    frequency_hz: float
    ra_hours: float
    dec_degrees: float
    time_begin: str
    time_end: str
    gap_tolerance_seconds: int = 30
    gain_cutoff_percent: float = 3.0
    data_type: str = "active"
    concurrency_level: int = field(default_factory=os.cpu_count)