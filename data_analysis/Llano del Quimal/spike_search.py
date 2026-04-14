"""
Llano del Quimal — RFI Spike Search
=====================================
Scans every spectrum across all three setups for narrowband spikes
that stand significantly above the local noise floor.

Method (matching Monte Salto methodology):
  - For each spectrum, compute a rolling median across a 51-bin window
    (~51 x freq_step) as the local baseline.
  - A bin is flagged if  power > baseline + THRESHOLD_DB.
  - Contiguous flagged bins are merged into a single "spike" event.
  - Results are tabulated and plotted.

Default threshold: 10 dB (to catch everything; 30 dB highlighted separately).
"""

import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.ndimage import uniform_filter1d

# ── config ────────────────────────────────────────────────────────────────────
BASE_DIR      = Path(__file__).parent
OUTPUT_DIR    = Path(r"C:\Users\hijox\Documents\UNI\Final Year Project\Program Images\analysis for paper\llano")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SETUPS        = ["first setup", "second setup", "third setup"]
POL_ORDER     = ["0deg", "90deg"]
BASELINE_BINS = 51      # rolling median window (bins)
THRESHOLD_DB  = 10.0    # minimum excess to flag
HIGHLIGHT_DB  = 30.0    # "strong spike" threshold (like Monte Salto 14.495 GHz)

plt.rcParams.update({
    "figure.dpi": 150, "savefig.dpi": 200,
    "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
    "legend.fontsize": 8, "figure.constrained_layout.use": True,
})

# ── helpers ───────────────────────────────────────────────────────────────────

def parse_timestamp(stem):
    m = re.search(r"(?:EOS)?(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})(\d{3})", stem)
    if not m:
        return pd.NaT
    y, mo, d, hh, mi, ss, ms = map(int, m.groups())
    return pd.Timestamp(y, mo, d, hh, mi, ss) + pd.Timedelta(milliseconds=ms)


def assign_pol_pointing(files):
    """Return list of (path, pol, pointing_idx) sorted by timestamp."""
    rows = [(p, parse_timestamp(p.stem)) for p in files]
    rows.sort(key=lambda x: x[1])
    result = []
    for i, (p, ts) in enumerate(rows):
        pol = POL_ORDER[i % len(POL_ORDER)]
        pointing_idx = i // len(POL_ORDER)
        result.append((p, pol, pointing_idx, ts))
    return result


def rolling_median_baseline(power_arr, window=BASELINE_BINS):
    """Compute a robust local baseline via a sliding median."""
    from numpy.lib.stride_tricks import sliding_window_view
    half = window // 2
    padded = np.pad(power_arr, (half, half), mode="edge")
    windows = sliding_window_view(padded, window)
    return np.median(windows, axis=1)


def find_spikes(freqs, power, threshold_db=THRESHOLD_DB):
    """
    Returns a list of dicts, one per contiguous spike group:
      freq_peak, power_peak, baseline_at_peak, excess_db,
      freq_lo, freq_hi, n_bins
    """
    baseline = rolling_median_baseline(power)
    excess   = power - baseline
    flagged  = excess >= threshold_db

    spikes = []
    in_spike = False
    for i, flag in enumerate(flagged):
        if flag and not in_spike:
            start = i
            in_spike = True
        elif not flag and in_spike:
            seg = slice(start, i)
            peak_i = start + int(np.argmax(power[seg]))
            spikes.append({
                "freq_peak_GHz": freqs[peak_i],
                "power_peak_dBm": power[peak_i],
                "baseline_dBm": baseline[peak_i],
                "excess_dB": excess[peak_i],
                "freq_lo_GHz": freqs[start],
                "freq_hi_GHz": freqs[i - 1],
                "n_bins": i - start,
            })
            in_spike = False
    if in_spike:
        seg = slice(start, len(freqs))
        peak_i = start + int(np.argmax(power[seg]))
        spikes.append({
            "freq_peak_GHz": freqs[peak_i],
            "power_peak_dBm": power[peak_i],
            "baseline_dBm": baseline[peak_i],
            "excess_dB": excess[peak_i],
            "freq_lo_GHz": freqs[start],
            "freq_hi_GHz": freqs[-1],
            "n_bins": len(freqs) - start,
        })
    return spikes, baseline


# ══════════════════════════════════════════════════════════════════════════════
# SCAN ALL FILES
# ══════════════════════════════════════════════════════════════════════════════
print("Scanning all spectra for spikes …\n")

all_spikes = []

for setup in SETUPS:
    csv_dir = BASE_DIR / setup
    files   = sorted(csv_dir.glob("EOS*.csv"))
    entries = assign_pol_pointing(files)
    print(f"  {setup}: {len(entries)} spectra")

    for path, pol, pointing_idx, ts in entries:
        df    = pd.read_csv(path)
        freqs = df["frequency_Hz"].values / 1e9
        power = df["power_dBm"].values
        spikes, _ = find_spikes(freqs, power)
        for s in spikes:
            all_spikes.append({
                "setup": setup,
                "file": path.name,
                "timestamp": ts,
                "pol": pol,
                "pointing_idx": pointing_idx,
                **s,
            })

spikes_df = pd.DataFrame(all_spikes)
print(f"\nTotal spike events detected (>{THRESHOLD_DB} dB above local baseline): {len(spikes_df)}")

strong_df = spikes_df[spikes_df["excess_dB"] >= HIGHLIGHT_DB]
print(f"Strong spikes (>{HIGHLIGHT_DB} dB): {len(strong_df)}")

# ══════════════════════════════════════════════════════════════════════════════
# PRINT SUMMARY TABLE
# ══════════════════════════════════════════════════════════════════════════════

print("\n=== All spikes sorted by excess (top 60) ===")
cols = ["setup", "pol", "pointing_idx", "freq_peak_GHz", "power_peak_dBm",
        "baseline_dBm", "excess_dB", "n_bins"]
top = spikes_df.sort_values("excess_dB", ascending=False).head(60)
print(top[cols].to_string(index=False))

if len(strong_df):
    print(f"\n=== Spikes >= {HIGHLIGHT_DB} dB above baseline ===")
    print(strong_df[cols].to_string(index=False))

# ══════════════════════════════════════════════════════════════════════════════
# CHART A — Spike excess vs frequency (scatter, all setups)
# ══════════════════════════════════════════════════════════════════════════════
print("\nGenerating plots …")

setup_colors = {
    "first setup":  "#555555",
    "second setup": "#1f77b4",
    "third setup":  "#d62728",
}

fig, ax = plt.subplots(figsize=(14, 5))
for setup in SETUPS:
    sub = spikes_df[spikes_df["setup"] == setup]
    ax.scatter(sub["freq_peak_GHz"], sub["excess_dB"],
               color=setup_colors[setup], s=18, alpha=0.6,
               label=setup.title())

ax.axhline(HIGHLIGHT_DB, color="red", linestyle="--", linewidth=1,
           label=f"{HIGHLIGHT_DB} dB threshold")
ax.set_xlabel("Spike frequency (GHz)")
ax.set_ylabel(f"Excess above local baseline (dB)")
ax.set_title(f"RFI Spikes — Excess vs Frequency (all setups, threshold >= {THRESHOLD_DB} dB)")
ax.legend()
ax.grid(True, alpha=0.3)
fig.savefig(OUTPUT_DIR / "spike_excess_vs_freq.png", bbox_inches="tight")
plt.close(fig)
print("  saved -> spike_excess_vs_freq.png")

# ══════════════════════════════════════════════════════════════════════════════
# CHART B — Spike excess vs pointing index (do spikes correlate with heading?)
# ══════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 3, figsize=(16, 5), sharey=False)
fig.suptitle("Spike Excess vs Pointing Index (per setup)", fontweight="bold")

for ax, setup in zip(axes, SETUPS):
    sub = spikes_df[spikes_df["setup"] == setup]
    for pol, marker, col in [("0deg", "o", "#1f77b4"), ("90deg", "s", "#d62728")]:
        p = sub[sub["pol"] == pol]
        ax.scatter(p["pointing_idx"], p["excess_dB"],
                   marker=marker, color=col, s=18, alpha=0.7, label=f"Pol {pol}")
    ax.axhline(HIGHLIGHT_DB, color="red", linestyle="--", linewidth=1)
    ax.set_title(setup.title(), fontsize=9)
    ax.set_xlabel("Pointing index")
    ax.set_ylabel("Excess above baseline (dB)")
    ax.legend()
    ax.grid(True, alpha=0.3)

fig.savefig(OUTPUT_DIR / "spike_excess_vs_pointing.png", bbox_inches="tight")
plt.close(fig)
print("  saved -> spike_excess_vs_pointing.png")

# ══════════════════════════════════════════════════════════════════════════════
# CHART C — Frequency histogram of spike occurrences (how often each freq spikes)
# ══════════════════════════════════════════════════════════════════════════════
fig, axes = plt.subplots(1, 3, figsize=(16, 4))
fig.suptitle(f"Spike Frequency Histogram (>=  {THRESHOLD_DB} dB excess)", fontweight="bold")

for ax, setup in zip(axes, SETUPS):
    sub = spikes_df[spikes_df["setup"] == setup]
    if len(sub) == 0:
        ax.set_title(setup.title())
        continue
    fmin = sub["freq_peak_GHz"].min()
    fmax = sub["freq_peak_GHz"].max()
    bins = np.linspace(fmin, fmax, 100)
    ax.hist(sub["freq_peak_GHz"], bins=bins,
            color=setup_colors[setup], alpha=0.8, edgecolor="none")
    ax.set_title(setup.title(), fontsize=9)
    ax.set_xlabel("Frequency (GHz)")
    ax.set_ylabel("Spike count")
    ax.grid(True, alpha=0.3)

fig.savefig(OUTPUT_DIR / "spike_frequency_histogram.png", bbox_inches="tight")
plt.close(fig)
print("  saved -> spike_frequency_histogram.png")

# ══════════════════════════════════════════════════════════════════════════════
# CHART D — Detailed spectrum plot for the top N strongest spikes
# ══════════════════════════════════════════════════════════════════════════════
TOP_N = 12
top_spikes = spikes_df.sort_values("excess_dB", ascending=False).head(TOP_N)

fig, axes = plt.subplots(3, 4, figsize=(18, 12))
fig.suptitle(f"Top {TOP_N} Strongest RFI Spikes — Spectrum Detail", fontweight="bold")
axes = axes.flatten()

for ax, (_, row) in zip(axes, top_spikes.iterrows()):
    setup   = row["setup"]
    path    = BASE_DIR / setup / row["file"]
    df      = pd.read_csv(path)
    freqs   = df["frequency_Hz"].values / 1e9
    power   = df["power_dBm"].values
    _, baseline = find_spikes(freqs, power)

    # zoom window: ±200 bins around peak
    peak_bin = int(np.argmin(np.abs(freqs - row["freq_peak_GHz"])))
    lo = max(0, peak_bin - 200)
    hi = min(len(freqs), peak_bin + 200)
    f_win = freqs[lo:hi]
    p_win = power[lo:hi]
    b_win = baseline[lo:hi]

    ax.plot(f_win, p_win, linewidth=0.8, color=setup_colors[setup], label="Power")
    ax.plot(f_win, b_win, linewidth=1.0, color="black", linestyle="--",
            alpha=0.6, label="Baseline")
    ax.axvline(row["freq_peak_GHz"], color="red", linewidth=0.8, linestyle=":")
    ax.scatter([row["freq_peak_GHz"]], [row["power_peak_dBm"]],
               color="red", s=30, zorder=5)
    ax.annotate(f"{row['excess_dB']:.1f} dB\n{row['freq_peak_GHz']:.4f} GHz",
                xy=(row["freq_peak_GHz"], row["power_peak_dBm"]),
                xytext=(8, -12), textcoords="offset points",
                fontsize=7, color="red",
                arrowprops=dict(arrowstyle="->", lw=0.7, color="red"))

    title = (f"{setup.title()} | idx {int(row['pointing_idx'])} | {row['pol']}\n"
             f"{row['freq_peak_GHz']:.4f} GHz | +{row['excess_dB']:.1f} dB")
    ax.set_title(title, fontsize=7.5)
    ax.set_xlabel("Frequency (GHz)", fontsize=7)
    ax.set_ylabel("Power (dBm)", fontsize=7)
    ax.tick_params(labelsize=6)
    ax.grid(True, alpha=0.25)
    ax.legend(fontsize=6)

fig.savefig(OUTPUT_DIR / "spike_top_spectra_detail.png", bbox_inches="tight")
plt.close(fig)
print("  saved -> spike_top_spectra_detail.png")

# ══════════════════════════════════════════════════════════════════════════════
# CHART E — 2.15 GHz spike deep-dive: excess vs pointing index
# ══════════════════════════════════════════════════════════════════════════════
# Focus on the ~2.135 GHz persistent feature seen in setup 2
SPIKE_FREQ_LO = 2.10
SPIKE_FREQ_HI = 2.18

setup2_spikes = spikes_df[
    (spikes_df["setup"] == "second setup") &
    (spikes_df["freq_peak_GHz"] >= SPIKE_FREQ_LO) &
    (spikes_df["freq_peak_GHz"] <= SPIKE_FREQ_HI)
].copy()

if len(setup2_spikes):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    fig.suptitle("2.10–2.18 GHz Feature — Setup 2 (L-band LNA)", fontweight="bold")

    for pol, marker, col in [("0deg", "o", "#1f77b4"), ("90deg", "s", "#d62728")]:
        p = setup2_spikes[setup2_spikes["pol"] == pol]
        ax1.scatter(p["pointing_idx"], p["excess_dB"],
                    marker=marker, color=col, s=30, label=f"Pol {pol}")
        ax2.scatter(p["pointing_idx"], p["freq_peak_GHz"],
                    marker=marker, color=col, s=30, label=f"Pol {pol}")

    ax1.axhline(HIGHLIGHT_DB, color="red", linestyle="--", linewidth=1,
                label=f"{HIGHLIGHT_DB} dB threshold")
    ax1.set_xlabel("Pointing index")
    ax1.set_ylabel("Excess above local baseline (dB)")
    ax1.set_title("Spike Excess vs Pointing Index")
    ax1.legend(); ax1.grid(True, alpha=0.3)

    ax2.set_xlabel("Pointing index")
    ax2.set_ylabel("Peak frequency (GHz)")
    ax2.set_title("Spike Frequency vs Pointing Index\n(stable = fixed transmitter; drifting = satellite)")
    ax2.legend(); ax2.grid(True, alpha=0.3)

    fig.savefig(OUTPUT_DIR / "spike_2135MHz_detail.png", bbox_inches="tight")
    plt.close(fig)
    print("  saved -> spike_2135MHz_detail.png")

    # Also print the full table for this feature
    print(f"\n=== 2.10–2.18 GHz feature detail (setup 2, {len(setup2_spikes)} events) ===")
    print(setup2_spikes[["pol", "pointing_idx", "freq_peak_GHz",
                          "power_peak_dBm", "baseline_dBm", "excess_dB"]]
          .sort_values("pointing_idx").to_string(index=False))

# Save full spike table to CSV for reference
spikes_df.sort_values("excess_dB", ascending=False).to_csv(
    OUTPUT_DIR / "spike_results.csv", index=False
)
print(f"\nFull spike table saved -> spike_results.csv")
print(f"\nAll done. PNGs saved to:\n  {OUTPUT_DIR}")
