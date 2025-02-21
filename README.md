## Overview
This Python script tracks the apparent position of an astronomical target as seen from a ground station and checks for potential satellite intersections. It then visualises the results in a 3D plot. The script uses the Skyfield library for precise celestial mechanics calculations.

## Functions

### 1. `checkTargetPosition(t, target)`
Determines the apparent position of a celestial target from the observing station at a given time `t`.

#### Inputs:
- `t`: A Skyfield time object
- `target`: A Skyfield Star object

#### Returns:
- The apparent position of the target in the sky (altitude, azimuth, etc.).

---

### 2. `timeRange(target, t_init, t_end)`
Tracks the target over a given time range and logs its position every second. It also checks for satellite intersections.

#### Inputs:
- `target`: The celestial object being observed
- `t_init`: Start time (Skyfield time object)
- `t_end`: End time (Skyfield time object)

#### Outputs:
- Prints the altitude and azimuth of the target for each second.
- Checks for satellites within a 2-degree range.
- Calls `plot_3d()` to visualise data.

---

### 3. `checkSatelliteIntersect(t, target, targPos)`
Determines whether any satellites are near the target at a given time.

#### Inputs:
- `t`: Current time
- `target`: The celestial object
- `targPos`: Apparent position of the target

#### Returns:
- A list of satellites that pass within 2 degrees of the target.

---

### 4. `plot_3d(times, alts, azs, sat_times, sat_alts, sat_azs)`
Creates a 3D plot of the target’s trajectory and any intersecting satellites.

#### Inputs:
- Lists of timestamps, altitudes, and azimuths for the target and satellites

#### Output:
- A 3D visualisation using `matplotlib`.

---

### 5. `selectData(type)`
Downloads and loads satellite data from Celestrak.

#### Inputs:
- `type`: The type of satellites (e.g., "starlink" or "stations")

#### Outputs:
- Returns a list of `EarthSatellite` objects.
- Saves the latest satellite data as a CSV file, refreshing every 7 days.

---

### 6. `main()`
- Loads planetary and satellite data.
- Defines the observing location.
- Defines the target.
- Calls `timeRange()` to track the target and execute all functions listed above.

## Notes
- The script is currently configured to observe the Vela quasar from Warkworth, NZ (as of 21/02/25).
- The 2-degree threshold for satellite detection can be adjusted in `checkSatelliteIntersect()`.
- The script prints relevant information to the console and visualises it in a 3D plot.

