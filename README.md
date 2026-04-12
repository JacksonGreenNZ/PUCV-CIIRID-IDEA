# Satellite RFI Predictor

A desktop application for predicting radio frequency interference (RFI) from satellite constellations during radio astronomy observations. Given an observatory location, observation target, and time window, it identifies clean stretches of time where no satellites pass through the telescope beam.

<p align="center"><a href="https://github.com/JacksonGreenNZ/PUCV-CIIRID-IDEA/releases/download/v0.0.3/clearskyrfi-0.0.3-amd64.deb"> <img width="202" height="39" alt="linuxinst" src="https://github.com/user-attachments/assets/002f72be-32bf-4eaf-b72f-52c452901034" /></a>&nbsp;&nbsp;&nbsp;
<a href="https://github.com/JacksonGreenNZ/PUCV-CIIRID-IDEA/releases/download/v0.0.3/ClearSkyRFI-Setup.exe"> <img width="247" height="39" alt="wininst" src="https://github.com/user-attachments/assets/23e98fa0-e8db-4399-bd84-2e20b03052ae" /></a>&nbsp;&nbsp;&nbsp;
<a href="https://github.com/JacksonGreenNZ/PUCV-CIIRID-IDEA/releases/download/v0.0.3/ClearSkyRFI-0.0.3-macos.dmg"><img width="223" height="39" alt="macos" src="https://github.com/user-attachments/assets/2ad2dfbb-a3a4-4470-b6d3-cf7c9ad2e10f" /> </a> </p>


---

## Features

- **Observatory configuration** — latitude, longitude, elevation, dish diameter, frequency, gain cutoff
- **Target selection** — celestial tracking (RA/Dec) or fixed pointing (Az/Alt)
- **Flexible beam modelling** — Airy diffraction pattern or manual beamwidth
- **Satellite pre-filtering** — via SOPP, using the computed Airy radius as the search cone
- **Clean stretch analysis** — identifies contiguous interference-free periods, linked across configurable gaps
- **CSV export** — per-event interference data with timestamp, satellite, angular separation, and gain
- **Sky animation** — dual-hemisphere visualisation of satellite trajectories and target track

---

## Computational Approach

### 1. TLE Acquisition
Satellite orbital elements are downloaded from [CelesTrak](https://celestrak.org/NORAD/elements/) and cached locally, refreshed automatically if older than 7 days.

### 2. Beam Modelling
The telescope beam is modelled as an Airy diffraction pattern:

$$G(\theta) = \left[\frac{2J_1(\pi D \sin\theta / \lambda)}{\pi D \sin\theta / \lambda}\right]^2$$

The outermost angle at which gain exceeds the configured cutoff threshold defines the pre-filter search radius passed to SOPP.

Alternatively, a manual beamwidth can be specified directly, bypassing the Airy model entirely.

### 3. Target Position Precomputation
Target altitude and azimuth are precomputed at 1-second resolution across the observation window using [Skyfield](https://rhodesmill.org/skyfield/) and the DE421 planetary ephemeris. For fixed pointing, the az/alt is held constant.

### 4. Satellite Pre-filtering (SOPP)
[SOPP](https://github.com/niwcpac/sopp) propagates all catalogue satellites and returns only those passing within the pre-filter cone during the observation window.

### 5. Interference Detection
For each candidate satellite position, angular separation from the target is computed via the haversine formula. Separation is converted to fractional beam gain via the Airy pattern; timesteps exceeding the gain threshold are flagged.

### 6. Clean Stretch Analysis
Flagged timestamps are used to identify contiguous clean periods. Clean stretches within a configurable gap tolerance are linked into ranked usable observing blocks.

---

## Output

| Format | Description |
|---|---|
| CSV | Per-event data: timestamp, satellite name, positions, angular separation, gain percentage |
| MP4 | Dual-hemisphere sky animation: full sky view and beam-centred relative view |

Files are saved to the `outputs/` directory with timestamp-based naming:
- `sat_intersect_YYYY-MM-DD_HH-MM-SS.csv`
- `sky_plot_YYYY-MM-DD_HH-MM-SS.mp4`

---

## Data Sources

| Source | Usage |
|---|---|
| [CelesTrak](https://celestrak.org/NORAD/elements/) | Satellite TLE catalogues |
| [DE421](https://rhodesmill.org/skyfield/planets.html) | Planetary ephemeris for target position computation |

---

## Platform Support

| Platform | Status |
|---|---|
| Linux | Supported |
| Windows (WSL) | Supported |
| Windows (native) | Supported |
| macOS | In progress |

---

## Testing
```bash
pytest tests/ -v
```

Unit tests cover beam modelling, angular separation, window analysis, interference detection, and application state. Integration testing (SOPP, Skyfield, Celestrak) is performed manually.

---

## Acknowledgements

Developed in collaboration with the the physics department at PUCV.
