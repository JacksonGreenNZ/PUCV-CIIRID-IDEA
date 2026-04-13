"""
La Serena RFI Spike Analysis
============================
Investigates satellite positions relative to the antenna beam during the
observed RFI spike at ~13:06 UTC on 2026-01-21.

Uses the correct Jan 21 satellite intersection data
(sat_intersect_2026-04-12_20-39-25.csv). An earlier version of this script
incorrectly used Jan 26 prediction data; see git history if needed.

Target direction: azimuth 240 degrees, elevation 0 degrees (horizon).
Beam model: Gaussian with FWHM = 60 degrees (consistent with prior analysis scripts).

--- Spike localisation (derived in la_serena_spike_combined.py) ---
Spike EOS file   : EOS20260121100540972.csv
File start (UTC) : 2026-01-21 13:05:40  (local 10:05:40 + UTC-3 offset)
Scan parameters  : 1000 frequency bins over ~51.727 s mean scan duration
                   (mean of 44 single-scan gaps in the 50-52 s range)
Time per bin     : 51.727 / 1000 = 51.727 ms
Spike frequency  : 14.495 GHz  (bin index 963 of 1000, peak power 4.52 dBm,
                   ~60 dB above the baseline of ~-57 dBm)
Time to spike    : 963 x 0.051727 s = 49.813 s after file start
Estimated spike  : 2026-01-21 13:06:29.8 UTC

Satellite context (from Jan 21 TLEs, payloads only, deduplicated):
  Closest at spike time (13:06:29 UTC): STARLINK-1019 at 2.63 degrees
    (alt 1.13 deg, az 237.6 deg).
  Second closest: LEGION 6 (AST SpaceMobile) at 2.78 degrees.
  Both operate in Ku-band and are credible RFI sources at 14.495 GHz.
  Earlier runs with incorrect (April 2026) TLEs gave wrong results;
  this file uses Space-Track gp_history TLEs with epoch closest to
  2026-01-21 13:06 UTC, deduplicated to one TLE per satellite.
  
  https://www.space-track.org/basicspacedata/query/class/gp_history/EPOCH/2026-01-20--2026-01-22/OBJECT_TYPE/PAYLOAD/format/3le
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DATA_FILE  = r"ClearSkyRFIData202601211301.csv"
OUT_DIR    = r"C:\Users\hijox\Documents\UNI\Final Year Project\Program Images\analysis for paper"
SPIKE_TIME = pd.Timestamp("2026-01-21T13:06:29+00:00")  # refined to 13:06:29.8 UTC
FWHM       = 60.0
SIGMA      = FWHM / (2 * np.sqrt(2 * np.log(2)))
CLOSE_THRESHOLD_DEG = 15.0

def save(filename):
    plt.savefig(os.path.join(OUT_DIR, filename), dpi=150, bbox_inches="tight")

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
df = pd.read_csv(DATA_FILE)
df["time_utc"] = pd.to_datetime(df["time_utc"], utc=True)
df["satellite"] = df["satellite"].str.replace(r"^0 ", "", regex=True)  # strip 3LE name prefix
df["beam_weight"] = np.exp(-(df["angular_sep_deg"] ** 2) / (2 * SIGMA ** 2))

print(f"Loaded {len(df):,} rows covering {df['satellite'].nunique()} unique satellites")
print(f"Time range: {df['time_utc'].min()} to {df['time_utc'].max()}")

# ---------------------------------------------------------------------------
# 1. Beam-weighted satellite density over time
# ---------------------------------------------------------------------------
density_per_second = (
    df.groupby("time_utc")["beam_weight"]
    .sum()
    .reset_index()
    .rename(columns={"beam_weight": "beam_weighted_density"})
)

fig, ax = plt.subplots(figsize=(12, 4))
ax.plot(density_per_second["time_utc"], density_per_second["beam_weighted_density"],
        linewidth=1.5, color="steelblue", label="Beam-weighted satellite density")
ax.axvline(SPIKE_TIME, color="red", linestyle="--", linewidth=1.5,
           label="13:06:29 UTC — RFI spike (14.495 GHz)")
ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
ax.set_xlabel("UTC Time (2026-01-21)")
ax.set_ylabel("Beam-weighted density (a.u.)")
ax.set_title("Beam-weighted Satellite Density vs Time\n(higher = more satellite signal potentially entering beam)")
ax.legend()
ax.grid(True, alpha=0.4)
plt.tight_layout()
save("la_serena_beam_density.png")
plt.show()

# ---------------------------------------------------------------------------
# 2. Satellites within CLOSE_THRESHOLD_DEG at spike time
# ---------------------------------------------------------------------------
spike_window = df[
    (df["time_utc"] >= pd.Timestamp("2026-01-21T13:06:00+00:00"))
    & (df["time_utc"] <= pd.Timestamp("2026-01-21T13:06:59+00:00"))
]

close_during_spike = (
    spike_window[spike_window["angular_sep_deg"] <= CLOSE_THRESHOLD_DEG]
    .groupby("satellite")["angular_sep_deg"]
    .min()
    .sort_values()
    .reset_index()
    .rename(columns={"angular_sep_deg": "min_angular_sep_deg"})
)

print(f"\nSatellites within {CLOSE_THRESHOLD_DEG} deg of target during 13:06 window "
      f"({len(close_during_spike)} satellites):")
print(close_during_spike.to_string(index=False))

if len(close_during_spike) > 0:
    fig, ax = plt.subplots(figsize=(10, max(4, len(close_during_spike) * 0.35)))
    colors = ["crimson" if v < 5 else "darkorange" if v < 10 else "steelblue"
              for v in close_during_spike["min_angular_sep_deg"]]
    ax.barh(close_during_spike["satellite"], close_during_spike["min_angular_sep_deg"],
            color=colors)
    ax.axvline(CLOSE_THRESHOLD_DEG, color="black", linestyle="--", linewidth=1,
               label=f"{CLOSE_THRESHOLD_DEG} deg threshold")
    ax.set_xlabel("Minimum Angular Separation from Target (degrees)")
    ax.set_title("Satellites Closest to Beam During 13:06 UTC Spike Window\n"
                 "(red < 5 deg, orange < 10 deg, blue < 15 deg)")
    ax.legend()
    ax.grid(True, axis="x", alpha=0.4)
    plt.tight_layout()
    save("la_serena_close_satellites.png")
    plt.show()

# ---------------------------------------------------------------------------
# 3. Angular separation over time for the top closest satellites
#    Bad-data filter: exclude satellites whose altitude changes by more than
#    1 degree in a single second — physically impossible for a LEO satellite.
#
#    Two satellites were identified as having corrupt data:
#
#    STARLINK-36296: alternates between high (~20-29 deg) and low (~1-8 deg)
#      angular separation on a rigid ~15-second cycle, with altitude jumping
#      up to 14 deg/s. Likely caused by duplicate TLE entries for the same
#      satellite name in the source catalogue (e.g. Space-Track/CelesTrak),
#      one current and one stale, resulting in positions being computed from
#      two completely different orbital states interleaved under the same name.
#
#    STARLINK-30546: appears in bursts of 4-5 consecutive seconds every ~51
#      seconds, with elevation rising ~6-7 deg/s within each burst. The
#      ~51-second gap suggests the satellite was near the 30-deg cutoff
#      boundary during data generation, but the unphysical elevation rate
#      within bursts indicates a misassigned TLE — the catalogue entry for
#      this name likely corresponds to a different satellite in a different
#      orbital shell.
#
#    Both are TLE catalogue issues common in large Starlink constellations,
#    where SpaceX batch-launches cause temporary NORAD ID misassignments and
#    name reuse during the post-launch cataloguing process.
# ---------------------------------------------------------------------------
def is_bad_data(satellite_name):
    sat_df = df[df["satellite"] == satellite_name].sort_values("time_utc")
    if len(sat_df) < 2:
        return False
    alt_jumps = sat_df["sat_alt_deg"].diff().abs()
    return bool(alt_jumps.max() > 1.0)

clean_sats = [s for s in close_during_spike["satellite"] if not is_bad_data(s)]
top_n = min(10, len(clean_sats))
top_sats = clean_sats[:top_n]

fig, ax = plt.subplots(figsize=(12, 5))
for sat in top_sats:
    sat_df = df[df["satellite"] == sat].sort_values("time_utc")
    ax.plot(sat_df["time_utc"], sat_df["angular_sep_deg"], marker=".", markersize=3,
            linewidth=1.2, label=sat)

ax.axvline(SPIKE_TIME, color="red", linestyle="--", linewidth=1.5,
           label="13:06:29 UTC spike")
ax.axhline(CLOSE_THRESHOLD_DEG, color="black", linestyle=":", linewidth=1,
           label=f"{CLOSE_THRESHOLD_DEG} deg threshold")
ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
ax.set_xlabel("UTC Time (2026-01-21)")
ax.set_ylabel("Angular Separation from Target (degrees)")
ax.set_title(f"Angular Separation Over Time — Top {top_n} Closest Satellites at Spike")
ax.legend(fontsize=7, loc="upper left")
ax.grid(True, alpha=0.4)
plt.tight_layout()
save("la_serena_separation_over_time.png")
plt.show()

# ---------------------------------------------------------------------------
# 4. Sky plot at spike time
# ---------------------------------------------------------------------------
at_spike = df[
    (df["time_utc"] >= pd.Timestamp("2026-01-21T13:06:29+00:00"))
    & (df["time_utc"] <= pd.Timestamp("2026-01-21T13:06:30+00:00"))
].drop_duplicates("satellite")

fig, ax = plt.subplots(figsize=(10, 6))
scatter = ax.scatter(
    at_spike["sat_az_deg"],
    at_spike["sat_alt_deg"],
    c=at_spike["angular_sep_deg"],
    cmap="RdYlGn_r",
    s=40, vmin=0, vmax=30, zorder=3,
)
ax.scatter([240], [0], marker="*", s=250, color="red", zorder=5, label="Target (240 deg, 0 deg)")

for _, row in at_spike[at_spike["angular_sep_deg"] <= CLOSE_THRESHOLD_DEG].iterrows():
    ax.annotate(row["satellite"],
                xy=(row["sat_az_deg"], row["sat_alt_deg"]),
                fontsize=6, ha="left", va="bottom",
                xytext=(3, 3), textcoords="offset points")

cb = plt.colorbar(scatter, ax=ax)
cb.set_label("Angular Separation (degrees)")
ax.set_xlabel("Satellite Azimuth (degrees)")
ax.set_ylabel("Satellite Elevation (degrees)")
ax.set_title("Sky Plot at 13:06:29 UTC\n(colour = angular distance from target; red = close)")
ax.legend()
ax.grid(True, alpha=0.4)
plt.tight_layout()
save("la_serena_sky_plot.png")
plt.show()

# ---------------------------------------------------------------------------
# 5. Summary
# ---------------------------------------------------------------------------
print("\n--- Summary ---")
print(f"Spike window (13:06:00-13:06:59): {len(spike_window):,} satellite-second entries")
print(f"Satellites within {CLOSE_THRESHOLD_DEG} deg at spike: {len(close_during_spike)}")
if len(close_during_spike) > 0:
    closest = close_during_spike.iloc[0]
    print(f"Closest satellite: {closest['satellite']} "
          f"({closest['min_angular_sep_deg']:.2f} deg min separation)")

peak_density_time = density_per_second.loc[
    density_per_second["beam_weighted_density"].idxmax(), "time_utc"
]
print(f"Peak beam-weighted density at: {peak_density_time.strftime('%H:%M:%S')} UTC")
print(f"\nPlots saved to: {OUT_DIR}")