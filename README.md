# Satellite Interference Tracking System

## Abstract
This document describes a computational method for tracking satellite movement relative to a target celestial object from a fixed terrestrial observation point. The system determines instances where satellites may interfere with radio observation and generates visual and tabular representations of potential interferences.

## System Description
### Observation Parameters
- **Location** (e.g. Warkworth, New Zealand)
- **Target** (e.g., Vela quasar)
- **Observation Window**

### Data Sources
- **Planetary Ephemeris:** `de421.bsp`
- **Satellite Orbital Elements:** Retrieved from CelesTrak
- **Terrestrial Reference:** WGS84 geodetic coordinates, user defined

### Computational Approach
1. **Data Acquisition**
   - Planetary and satellite data are loaded.
   - Observation site parameters are established.
   
2. **Precomputation of Positions**
   - Vectorised time computations.
   - Satellite and target celestial object positions are precomputed to optimise processing.
   
3. **Satellite Intersection Detection**
   - Satellite positions are compared to the target’s location at each time step.
   - An intersection is registered if a satellite is within **0.7 degrees** of the target.
   
4. **Output Generation**
   - Intersection events are logged in a CSV file with the following parameters:
     - Timestamp
     - Object Name (Target/Satellite)
     - Altitude (degrees)
     - Azimuth (degrees)
     - Angular Separation (if applicable)
   - A 3D visualisation of satellite trajectories and the target’s motion is generated.

## Output Formats
### CSV Report
- Naming convention: `sat_intersect_YYYY-MM-DD_HH-MM-SS.csv`
- Provides tabular data on satellite interference events.

### Visualisation
- A 3D plot representing:
  - Target object trajectory
  - Satellite positions and potential interferences
  
## System Customisation
- **Satellite Database:** Change dataset selection in `selectData("x")` (e.g., "stations", "starlink", "active" etc).

## Applications
This system is applicable for astronomical observation planning and astrophotography scheduling in optical and radio astronomy.

