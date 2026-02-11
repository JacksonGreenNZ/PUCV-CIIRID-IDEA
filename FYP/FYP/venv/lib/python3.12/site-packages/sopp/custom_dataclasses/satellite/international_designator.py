from dataclasses import dataclass


@dataclass
class InternationalDesignator:
    year: int
    launch_number: int
    launch_piece: str

    def to_tle_string(self) -> str:
        return f'{str(self.year).zfill(2)}{str(self.launch_number).zfill(3)}{self.launch_piece}'

    @classmethod
    def from_tle_string(cls, tle_string: str) -> 'InternationalDesignator':
        return InternationalDesignator(
            year=int(tle_string[0:2]),
            launch_number=int(tle_string[2:5]),
            launch_piece=tle_string[5:].strip()
        )
