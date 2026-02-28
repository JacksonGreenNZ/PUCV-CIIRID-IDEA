import os

#hardcoded observer and target for testing based on sopp test file

#observer 
LATITUDE = 40.8
LONGITUDE = -121.4
ELEVATION_M = 986

#dish
DISH_DIAMETER_M = 20.0
FREQUENCY_HZ = 135e6

#observation target
RA_HOURS = 19 + 59/60
DEC_DEGREES = 40 + 44/60

#window
TIME_BEGIN = "2026-01-13T19:00:00"
TIME_END   = "2026-01-13T21:00:00"

#interference threshold
GAIN_CUTOFF_PERCENT = 1

#TLE catalogue
TLE_FILE = "data/active.tle"

#runtime settings
CONCURRENCY_LEVEL = os.cpu_count()