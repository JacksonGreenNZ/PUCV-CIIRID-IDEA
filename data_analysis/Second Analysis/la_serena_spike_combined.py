"""
La Serena RFI Spike — Combined Analysis
========================================
Cross-references the 1-15 GHz antenna spectrum files (EOS*.csv) taken at
azimuth 240 degrees with beam-weighted satellite density computed from the
satellite intersection data (sat_intersect_*.csv).

EOS file timestamps are in Chilean local time (UTC-3). The spike was observed
at ~13:06 UTC on 2026-01-21.

--- Spike localisation ---
EOS file timestamps are local Chilean time (UTC-3); +3 h gives UTC.
The 6 files at azimuth 240 degrees span 13:01:24 to 13:07:24 UTC,
covering 3 x pol-0 measurements followed by 3 x pol-90 measurements.

Spike EOS file   : EOS20260121100540972.csv  (pol 90, file start 13:05:40 UTC)
Scan parameters  : 1000 frequency bins, mean single-scan duration 51.727 s
                   (mean of 44 consecutive-file gaps in the 50-52 s range;
                    gaps of 100+ s indicate a polarisation or azimuth change)
Time per bin     : 51.727 / 1000 = 51.727 ms
Spike frequency  : 14.495 GHz  (bin index 963 of 1000, peak power 4.52 dBm,
                   ~60 dB above the ~-57 dBm baseline of all other files)
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
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import timezone, timedelta
import os

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SAT_FILE    = r"ClearSkyRFIData202601211301.csv"
DATA_FOLDER = r"antenna_readings/1-15 First setup.csv"
OUT_DIR     = r"C:\Users\hijox\Documents\UNI\Final Year Project\Program Images\analysis for paper"
UTC_OFFSET  = timedelta(hours=3)   # Chile summer time is UTC-3
FWHM        = 60.0
SIGMA       = FWHM / (2 * np.sqrt(2 * np.log(2)))
SPIKE_UTC   = pd.Timestamp("2026-01-21T13:06:29+00:00")  # refined to 13:06:29.8 UTC

# The 6 EOS files at azimuth 240 degrees (derived from data_analysis.py ordering)
EOS_240 = [
    ("EOS20260121100124579.csv", 0,  "13:01:24 UTC"),
    ("EOS20260121100216368.csv", 0,  "13:02:16 UTC"),
    ("EOS20260121100308169.csv", 0,  "13:03:08 UTC"),
    ("EOS20260121100450329.csv", 90, "13:04:50 UTC"),
    ("EOS20260121100540972.csv", 90, "13:05:40 UTC"),
    ("EOS20260121100724644.csv", 90, "13:07:24 UTC"),
]

# Convert local filename times to UTC timestamps for plotting
def local_to_utc(filename):
    """Extract timestamp from EOS filename and convert from local to UTC."""
    ts_str = filename[3:17]   # e.g. 20260121100124 (drop milliseconds)
    local_dt = pd.Timestamp(ts_str, tz=None)
    return local_dt + UTC_OFFSET

EOS_UTC = [(fn, pol, label, local_to_utc(fn)) for fn, pol, label in EOS_240]

# ---------------------------------------------------------------------------
# Load satellite intersection data
# ---------------------------------------------------------------------------
sat = pd.read_csv(SAT_FILE)
sat["time_utc"] = pd.to_datetime(sat["time_utc"], utc=True)
sat["satellite"] = sat["satellite"].str.replace(r"^0 ", "", regex=True)  # strip 3LE name prefix
sat["beam_weight"] = np.exp(-(sat["angular_sep_deg"] ** 2) / (2 * SIGMA ** 2))

density = (
    sat.groupby("time_utc")["beam_weight"]
    .sum()
    .reset_index()
    .rename(columns={"beam_weight": "density"})
)

print(f"Satellite data: {sat['time_utc'].min()} to {sat['time_utc'].max()}")
print(f"Peak density at: {density.loc[density['density'].idxmax(), 'time_utc']}")

# ---------------------------------------------------------------------------
# Load EOS spectra
# ---------------------------------------------------------------------------
spectra = []
for fn, pol, label, utc_ts in EOS_UTC:
    path = os.path.join(DATA_FOLDER, fn)
    df = pd.read_csv(path, header=None, skiprows=1, engine="python", sep=None)
    df = df.iloc[:, :2]
    df.columns = ["freq_Hz", "power_dBm"]
    df["freq_GHz"] = df["freq_Hz"] / 1e9
    spectra.append({"fn": fn, "pol": pol, "label": label, "utc": utc_ts, "df": df})
    print(f"{fn} | pol {pol:2d} | {label} | peak {df['power_dBm'].max():.2f} dBm")

# ---------------------------------------------------------------------------
# Figure 1: Beam-weighted density with EOS measurement markers
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(13, 5))
ax.plot(density["time_utc"], density["density"],
        color="steelblue", linewidth=1.5, label="Beam-weighted satellite density")
ax.axvline(SPIKE_UTC, color="red", linestyle="--", linewidth=1.5, label="~13:06 spike")

pol_colors = {0: "forestgreen", 90: "darkorange"}
for fn, pol, label, utc_ts in EOS_UTC:
    utc_ts_aware = utc_ts.tz_localize("UTC")
    ax.axvline(utc_ts_aware, color=pol_colors[pol], linestyle=":", linewidth=1.2)
    ax.text(utc_ts_aware, ax.get_ylim()[1] if ax.get_ylim()[1] != 1 else density["density"].max(),
            label, rotation=90, fontsize=7, va="top",
            color=pol_colors[pol])

# Add legend patches for polarisations
from matplotlib.patches import Patch
handles, labels_legend = ax.get_legend_handles_labels()
handles += [Patch(color="forestgreen", label="Pol 0 measurement"),
            Patch(color="darkorange",  label="Pol 90 measurement")]
ax.legend(handles=handles, fontsize=8)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
ax.set_xlabel("UTC Time (2026-01-21)")
ax.set_ylabel("Beam-weighted satellite density (a.u.)")
ax.set_title("Beam-weighted Satellite Density vs EOS Measurement Times\n(green = pol 0, orange = pol 90, dashed red = ~13:06 spike)")
ax.grid(True, alpha=0.4)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "combined_density_vs_eos_times.png"), dpi=150, bbox_inches="tight")
plt.show()

# ---------------------------------------------------------------------------
# Figure 2: Spectra for all 6 EOS files at 240 degrees
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(2, 3, figsize=(15, 8), sharey=True)
axes = axes.flatten()

for i, entry in enumerate(spectra):
    ax = axes[i]
    df = entry["df"]

    # Look up satellite density at this measurement time
    utc_aware = entry["utc"].tz_localize("UTC")
    # Find nearest second in density series
    time_diffs = (density["time_utc"] - utc_aware).abs()
    if time_diffs.min() < pd.Timedelta(seconds=5):
        nearest_density = density.loc[time_diffs.idxmin(), "density"]
        density_str = f"density={nearest_density:.2f}"
    else:
        density_str = "density=N/A"

    peak_power = df["power_dBm"].max()
    peak_freq  = df.loc[df["power_dBm"].idxmax(), "freq_GHz"]

    color = pol_colors[entry["pol"]]
    ax.plot(df["freq_GHz"], df["power_dBm"], color=color, linewidth=0.8)
    ax.scatter([peak_freq], [peak_power], color="red", s=30, zorder=5)
    ax.annotate(f"{peak_power:.1f} dBm\n@ {peak_freq:.3f} GHz",
                xy=(peak_freq, peak_power), xytext=(5, -15),
                textcoords="offset points", fontsize=7,
                arrowprops=dict(arrowstyle="->", lw=0.8))

    ax.set_title(f"{entry['label']}  |  pol {entry['pol']}°\n{density_str}", fontsize=9)
    ax.set_xlabel("Frequency (GHz)", fontsize=8)
    ax.set_ylabel("Power (dBm)", fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.tick_params(labelsize=7)

fig.suptitle("1-15 GHz Spectra at Azimuth 240° — Around 13:06 UTC Spike\n(green = pol 0°, orange = pol 90°)",
             fontsize=11)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "combined_spectra_240deg.png"), dpi=150, bbox_inches="tight")
plt.show()

# ---------------------------------------------------------------------------
# Figure 3: Mean power per measurement vs satellite density at that time
# ---------------------------------------------------------------------------
summary = []
for entry in spectra:
    utc_aware = entry["utc"].tz_localize("UTC")
    time_diffs = (density["time_utc"] - utc_aware).abs()
    nearest_density = density.loc[time_diffs.idxmin(), "density"] if time_diffs.min() < pd.Timedelta(seconds=5) else np.nan
    summary.append({
        "label": entry["label"],
        "pol": entry["pol"],
        "utc": utc_aware,
        "mean_power": entry["df"]["power_dBm"].mean(),
        "peak_power": entry["df"]["power_dBm"].max(),
        "sat_density": nearest_density,
    })

sdf = pd.DataFrame(summary)
print("\n--- EOS measurements at 240 degrees ---")
print(sdf[["label", "pol", "mean_power", "peak_power", "sat_density"]].to_string(index=False))

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

x = range(len(sdf))
xticks = sdf["label"].tolist()
bar_colors = [pol_colors[p] for p in sdf["pol"]]

ax1.bar(x, sdf["sat_density"], color=bar_colors, alpha=0.8)
ax1.set_ylabel("Beam-weighted satellite density")
ax1.set_title("Satellite Density and Antenna Power at Each 240 Measurement")
ax1.grid(True, axis="y", alpha=0.4)

ax2.bar(x, sdf["mean_power"], color=bar_colors, alpha=0.8)
ax2.set_ylabel("Mean power across 1-15 GHz (dBm)")
ax2.set_xlabel("Measurement time (UTC)")
ax2.grid(True, axis="y", alpha=0.4)

plt.xticks(list(x), xticks, rotation=15, fontsize=8)
from matplotlib.patches import Patch
fig.legend(handles=[Patch(color="forestgreen", label="Pol 0"),
                    Patch(color="darkorange",  label="Pol 90")],
           loc="upper right", fontsize=8)
plt.tight_layout()
plt.savefig(os.path.join(OUT_DIR, "combined_power_vs_density.png"), dpi=150, bbox_inches="tight")
plt.show()