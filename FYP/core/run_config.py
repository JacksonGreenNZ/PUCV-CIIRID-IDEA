import os
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class RunConfig:
    latitude: float
    longitude: float
    elevation_m: float
    dish_diameter_m: float
    frequency_hz: float
    time_begin: str
    time_end: str
    # pointing mode — one of these pairs must be set
    ra_hours: Optional[float] = None
    dec_degrees: Optional[float] = None
    azimuth_deg: Optional[float] = None
    altitude_deg: Optional[float] = None
    bypass_airy: bool = False
    manual_beamwidth_deg: float = 3.0
    # defaults
    gap_tolerance_seconds: int = 30
    gain_cutoff_percent: float = 3.0
    data_type: str = "active"
    concurrency_level: int = field(default_factory=os.cpu_count)
    

    def is_static(self) -> bool:
        return self.azimuth_deg is not None and self.altitude_deg is not None

    def is_tracking(self) -> bool:
        return self.ra_hours is not None and self.dec_degrees is not None