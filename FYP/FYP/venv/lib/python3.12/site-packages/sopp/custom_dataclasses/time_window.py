from dataclasses import dataclass
from datetime import datetime, timedelta

'''
The TimeWindow class is used to store the beginning and end time of events. The duration function returns a time delta for the 
duration of the event and the overlaps function determines if the TimeWindow overlaps with another TimeWindow
'''

@dataclass
class TimeWindow:
    begin: datetime
    end: datetime

    @property
    def duration(self) -> timedelta:
        return self.end - self.begin

    def overlaps(self, time_window: 'TimeWindow'):
        return self.begin < time_window.end and self.end > time_window.begin

    def __str__(self):
        return (
            f'{self.__class__.__name__}:\n'
            f'  Begin:              {self.begin}\n'
            f'  End:                {self.end}'
        )
