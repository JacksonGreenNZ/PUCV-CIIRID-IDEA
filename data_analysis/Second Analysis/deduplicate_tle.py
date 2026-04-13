"""
Deduplicate TLE file
====================
When Space-Track gp_history returns multiple TLE epochs for the same satellite,
each one gets loaded and produces duplicate position calculations.
This script keeps only the TLE whose epoch is closest to a target date.
"""

from datetime import datetime, timedelta

INPUT_TLE  = r"C:\Users\hijox\.clearskyrfi\data\payloads.tle"
OUTPUT_TLE = r"C:\Users\hijox\.clearskyrfi\data\active.tle"
TARGET_DATE = datetime(2026, 1, 21, 13, 6)  # centre of the observation window

def parse_epoch(tle_line1):
    """Parse epoch from TLE line 1 into a datetime."""
    epoch_str = tle_line1[18:32].strip()
    year_2digit = int(epoch_str[:2])
    year = 2000 + year_2digit if year_2digit < 57 else 1900 + year_2digit
    day_of_year = float(epoch_str[2:])
    return datetime(year, 1, 1) + timedelta(days=day_of_year - 1)

# Read all 3-line entries
with open(INPUT_TLE, encoding="utf-8", errors="replace") as f:
    raw = [l.rstrip("\n") for l in f.readlines()]

entries = []
i = 0
while i <= len(raw) - 3:
    name = raw[i].strip()
    l1   = raw[i+1].strip()
    l2   = raw[i+2].strip()
    if l1.startswith("1 ") and l2.startswith("2 "):
        try:
            epoch = parse_epoch(l1)
            entries.append((name, l1, l2, epoch))
        except Exception:
            pass
        i += 3
    else:
        i += 1

print(f"Total TLE entries loaded: {len(entries)}")

# Keep only the entry closest to TARGET_DATE per satellite name
best = {}
for name, l1, l2, epoch in entries:
    delta = abs((epoch - TARGET_DATE).total_seconds())
    if name not in best or delta < best[name][3]:
        best[name] = (name, l1, l2, delta)

print(f"Unique satellites after deduplication: {len(best)}")

# Write output
with open(OUTPUT_TLE, "w") as f:
    for name, l1, l2, _ in best.values():
        f.write(name + "\n")
        f.write(l1  + "\n")
        f.write(l2  + "\n")

print(f"Written to: {OUTPUT_TLE}")