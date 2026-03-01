# Satellite Interference Tracking System (WIP)

### Observation Parameters
- **Location** (LAT/LON/ELEVATION)
- **Target** (RA/DEC)
- **Observation Start/End Time**
- **Dish Diameter**
- **Frequency**
- **Window Gap Tolerance**
- **Gain Cutoff Percentage**
- **Satellite Catalogue**

Set in config.py file.

### Data Sources
- **Planetary Ephemeris:** `de421.bsp`
- **Satellite Orbital Elements:** Retrieved from CelesTrak in .tle format.

### Computational Approach
1. **Data Acquisition**
   - TLE satellite catalogue downloaded from Celestrak and cached locally (refreshed if older than 7 days).
   - Observer location and target coordinates loaded from configuration.

2. **Beam Modelling**
   - Telescope beam modelled as an Airy diffraction pattern: G(θ) = [2J₁(πD sinθ/λ) / (πD sinθ/λ)]²
   - Airy radius computed from dish diameter and observing frequency to define the pre-filter search cone.

3. **Precomputation of Positions**
   - Target altitude/azimuth precomputed at 1-second resolution across the observation window using Skyfield.

4. **Satellite Pre-filtering**
   - SOPP propagates all catalogue satellites and returns only those passing within the Airy search cone.

5. **Interference Detection**
   - Angular separation between each candidate satellite and the target computed via the haversine formula at each timestep.
   - Separation converted to fractional beam gain via the Airy pattern; timesteps exceeding the gain threshold are flagged.

6. **Clean Stretch Analysis**
   - Flagged timestamps used to identify contiguous clean periods within the observation window.
   - Clean stretches linked across short gaps (configurable tolerance) to produce ranked usable observing blocks.

7. **Output Generation**
   - Interference events written to CSV (timestamp, satellite name, angular separation, gain percentage).
   - Dual-hemisphere sky animation rendered showing satellite trajectories and target track.

## Output Formats
### CSV Report
- Naming convention: `sat_intersect_YYYY-MM-DD_HH-MM-SS.csv`, `sky_plot_YYYY-MM-DD_HH-MM-SS.mp4`
- Provides tabular data on satellite interference events.

### Visualisation
- Plots represent:
  - Satellite and target on observer sky.
  - Satellite positions relative to target.

## Applications
This system is applicable for astronomical observation planning and astrophotography scheduling in optical and radio astronomy.

