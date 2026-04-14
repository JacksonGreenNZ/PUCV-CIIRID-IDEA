"""
Llano del Quimal RFI Survey — Analysis & Plots
================================================
Three setups, each with 36 pointing indices × 2 polarisations (0°, 90°):
  first setup  : 1–15 GHz, ~14 MHz resolution, NO LNA
  second setup : 1–2.6 GHz, ~1.6 MHz resolution, L-band LNA
  third setup  : 5–11 GHz, ~6 MHz resolution, C/X-band LNA

Outputs (PNG) are saved to OUTPUT_DIR.
"""

import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.colors import Normalize
from pathlib import Path
from scipy.interpolate import interp1d

# ── paths ─────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
OUTPUT_DIR = Path(r"C:\Users\hijox\Documents\UNI\Final Year Project\Program Images\analysis for paper\llano")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SETUPS = ["first setup", "second setup", "third setup"]
SETUP_LABELS = {
    "first setup":  "Setup 1 (1–15 GHz, no LNA)",
    "second setup": "Setup 2 (1–2.6 GHz, L-band LNA)",
    "third setup":  "Setup 3 (5–11 GHz, C/X-band LNA)",
}
SETUP_COLORS = {
    "first setup":  "#555555",
    "second setup": "#1f77b4",
    "third setup":  "#d62728",
}

POL_ORDER      = ["0deg", "90deg"]
POL_LABELS     = {"0deg": "0°", "90deg": "90°"}
POL_COLORS     = {"0deg": "#1f77b4", "90deg": "#d62728"}
POL_LS         = {"0deg": "-",       "90deg": "--"}

REPEATS_PER_POL = 1
AZ0_DEG          = 0.0
DAZ_DEG          = 2.0

# ── matplotlib style ──────────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.dpi":      150,
    "savefig.dpi":     200,
    "font.size":       10,
    "axes.titlesize":  11,
    "axes.labelsize":  10,
    "legend.fontsize": 9,
    "figure.constrained_layout.use": True,
})

# ══════════════════════════════════════════════════════════════════════════════
# DATA LOADING
# ══════════════════════════════════════════════════════════════════════════════

def parse_timestamp(stem: str) -> pd.Timestamp:
    m = re.search(r"(?:EOS)?(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})(\d{3})", stem)
    if not m:
        return pd.NaT
    y, mo, d, hh, mi, ss, ms = map(int, m.groups())
    return pd.Timestamp(y, mo, d, hh, mi, ss) + pd.Timedelta(milliseconds=ms)


def assign_pol_pointing(g: pd.DataFrame) -> pd.DataFrame:
    g = g.sort_values(["timestamp", "file"]).reset_index(drop=True)
    block = REPEATS_PER_POL * len(POL_ORDER)
    i = np.arange(len(g))
    g["pol"]          = [POL_ORDER[(k // REPEATS_PER_POL) % len(POL_ORDER)] for k in i]
    g["pointing_idx"] = i // block
    g["az_deg"]       = (AZ0_DEG + g["pointing_idx"] * DAZ_DEG) % 360.0
    return g


def load_setup(setup_name: str) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """
    Returns:
        index   : DataFrame with columns [file, timestamp, pol, pointing_idx]
        freqs   : 1-D array of frequency values in GHz (1000,)
        power   : 3-D array [n_pointings, n_pols, n_freqs] in dBm
    """
    csv_dir   = BASE_DIR / setup_name
    csv_files = sorted(csv_dir.glob("EOS*.csv"))

    rows = []
    for p in csv_files:
        df = pd.read_csv(p)
        if {"frequency_Hz", "power_dBm"}.issubset(df.columns):
            rows.append({
                "file":      f"{p.parent.name}/{p.name}",
                "path":      p,
                "timestamp": parse_timestamp(p.stem),
            })

    index = pd.DataFrame(rows).sort_values(["timestamp", "file"]).reset_index(drop=True)
    index = assign_pol_pointing(index)

    # Build frequency axis from first file (all files in a setup share the same grid)
    sample = pd.read_csv(index.iloc[0]["path"])
    freqs  = sample["frequency_Hz"].values / 1e9          # GHz

    n_pointings = index["pointing_idx"].max() + 1
    n_pols      = len(POL_ORDER)
    n_freqs     = len(freqs)
    power       = np.full((n_pointings, n_pols, n_freqs), np.nan)

    for _, row in index.iterrows():
        df   = pd.read_csv(row["path"])
        pidx = int(row["pointing_idx"])
        pol  = POL_ORDER.index(row["pol"])
        power[pidx, pol, :] = df["power_dBm"].values

    return index, freqs, power


print("Loading data …")
data = {}
for s in SETUPS:
    print(f"  {s} …", end=" ", flush=True)
    idx, freqs, power = load_setup(s)
    data[s] = {"index": idx, "freqs": freqs, "power": power}
    print(f"OK  ({freqs[0]:.2f}–{freqs[-1]:.2f} GHz, {len(freqs)} bins, "
          f"{power.shape[0]} pointings)")

n_pointings = data["first setup"]["power"].shape[0]   # 36

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def save(fig: plt.Figure, name: str):
    path = OUTPUT_DIR / f"{name}.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved -> {path.name}")


def pointing_ticks(n=7):
    """Return ~7 evenly-spaced pointing indices and their azimuth labels."""
    idxs = np.round(np.linspace(0, n_pointings - 1, 7)).astype(int)
    labels = [str(i) for i in idxs]
    return idxs, labels


# ══════════════════════════════════════════════════════════════════════════════
# CHART 1 — Spectral Waterfall Heatmaps (one per setup, split by pol)
# ══════════════════════════════════════════════════════════════════════════════
print("\n[1/7] Waterfall heatmaps …")

for setup in SETUPS:
    freqs = data[setup]["freqs"]
    power = data[setup]["power"]   # (n_pointings, 2, n_freqs)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5), sharey=True)
    fig.suptitle(f"Spectral Waterfall — {SETUP_LABELS[setup]}", fontweight="bold")

    vmin = np.nanpercentile(power, 2)
    vmax = np.nanpercentile(power, 98)

    for ax, pol_idx, pol_name in zip(axes, [0, 1], POL_ORDER):
        im = ax.imshow(
            power[:, pol_idx, :],
            aspect="auto",
            origin="lower",
            extent=[freqs[0], freqs[-1], -0.5, n_pointings - 0.5],
            vmin=vmin, vmax=vmax,
            cmap="inferno",
            interpolation="nearest",
        )
        ax.set_title(f"Polarisation {POL_LABELS[pol_name]}")
        ax.set_xlabel("Frequency (GHz)")
        ax.set_ylabel("Pointing index (step = 2°)")

        # y-axis: pointing idx with az labels
        idxs, labels = pointing_ticks()
        ax.set_yticks(idxs)
        ax.set_yticklabels(labels)
        ax.set_ylabel("Pointing index")

        cb = fig.colorbar(im, ax=ax, shrink=0.85)
        cb.set_label("Power (dBm)")

    slug = setup.replace(" ", "_")
    save(fig, f"1_waterfall_{slug}")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 2 — Mean Spectrum per Setup (overlaid on shared axes)
# ══════════════════════════════════════════════════════════════════════════════
print("[2/7] Mean spectra overlay …")

# Two panels: left = 1–2.6 GHz (setup 1 & 2), right = 5–11 GHz (setup 1 & 3)
fig, (ax_l, ax_r) = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle("Mean Spectrum Across All Pointing Indices", fontweight="bold")

for ax, xlim, compared_setups in [
    (ax_l, (1.0, 2.6),  ["first setup", "second setup"]),
    (ax_r, (5.0, 11.0), ["first setup", "third setup"]),
]:
    for setup in compared_setups:
        freqs = data[setup]["freqs"]
        power = data[setup]["power"]
        mask  = (freqs >= xlim[0]) & (freqs <= xlim[1])
        if not mask.any():
            continue
        mean_pow = np.nanmean(power[:, :, mask], axis=(0, 1))  # avg over pointings & pols
        ax.plot(freqs[mask], mean_pow,
                color=SETUP_COLORS[setup],
                linewidth=0.8,
                label=SETUP_LABELS[setup],
                alpha=0.85)
    ax.set_xlim(xlim)
    ax.set_xlabel("Frequency (GHz)")
    ax.set_ylabel("Mean Power (dBm)")
    band = "1–2.6 GHz" if xlim == (1.0, 2.6) else "5–11 GHz"
    ax.set_title(f"Overlap band: {band}")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

save(fig, "2_mean_spectra_overlay")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 3 — LNA Gain vs Frequency
# ══════════════════════════════════════════════════════════════════════════════
print("[3/7] LNA gain profiles …")

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle("Effective LNA Gain (Setup with LNA − Setup without LNA)", fontweight="bold")

for ax, setup_lna, xlim, band_label in [
    (ax1, "second setup", (1.0, 2.6),  "L-band LNA (Setup 2 − Setup 1)"),
    (ax2, "third setup",  (5.0, 11.0), "C/X-band LNA (Setup 3 − Setup 1)"),
]:
    freqs_1   = data["first setup"]["freqs"]
    freqs_lna = data[setup_lna]["freqs"]
    power_1   = data["first setup"]["power"]
    power_lna = data[setup_lna]["power"]

    # restrict to overlap region
    mask_lna = (freqs_lna >= xlim[0]) & (freqs_lna <= xlim[1])
    f_lna    = freqs_lna[mask_lna]

    for pol_idx, pol_name in enumerate(POL_ORDER):
        mean_1   = np.nanmean(power_1[:, pol_idx, :], axis=0)   # (n_freqs_1,)
        mean_lna = np.nanmean(power_lna[:, pol_idx, mask_lna], axis=0)

        # interpolate setup-1 mean onto the LNA setup frequency grid
        interp = interp1d(freqs_1, mean_1, kind="linear", bounds_error=False, fill_value=np.nan)
        mean_1_interp = interp(f_lna)

        gain = mean_lna - mean_1_interp
        ax.plot(f_lna, gain,
                color=POL_COLORS[pol_name],
                linestyle=POL_LS[pol_name],
                linewidth=0.9,
                label=f"Pol {POL_LABELS[pol_name]}")

    ax.axhline(0, color="black", linewidth=0.6, linestyle=":")
    ax.set_xlim(xlim)
    ax.set_xlabel("Frequency (GHz)")
    ax.set_ylabel("Gain (dB)")
    ax.set_title(band_label)
    ax.legend()
    ax.grid(True, alpha=0.3)

save(fig, "3_lna_gain_profile")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 4 — With vs Without LNA at Fixed Pointing Index (idx=0)
# ══════════════════════════════════════════════════════════════════════════════
print("[4/7] LNA comparison at fixed pointing …")

FIXED_IDX = 0

fig, (ax_l, ax_r) = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle(f"With vs Without LNA — Pointing index {FIXED_IDX}", fontweight="bold")

for ax, xlim, setup_lna, band_label in [
    (ax_l, (1.0, 2.6),  "second setup", "L-band (1–2.6 GHz)"),
    (ax_r, (5.0, 11.0), "third setup",  "C/X-band (5–11 GHz)"),
]:
    for setup, ls, lw, alpha in [("first setup", "-", 1.0, 0.7), (setup_lna, "--", 1.2, 0.9)]:
        freqs = data[setup]["freqs"]
        power = data[setup]["power"]
        mask  = (freqs >= xlim[0]) & (freqs <= xlim[1])
        if not mask.any():
            continue
        for pol_idx, pol_name in enumerate(POL_ORDER):
            ax.plot(freqs[mask], power[FIXED_IDX, pol_idx, mask],
                    color=POL_COLORS[pol_name],
                    linestyle=ls, linewidth=lw, alpha=alpha,
                    label=f"{SETUP_LABELS[setup].split('(')[0].strip()} — pol {POL_LABELS[pol_name]}")

    ax.set_xlim(xlim)
    ax.set_xlabel("Frequency (GHz)")
    ax.set_ylabel("Power (dBm)")
    ax.set_title(band_label)
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)

save(fig, "4_lna_comparison_fixed_pointing")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 5 — Integrated Power vs Pointing Index (Beam Scan)
# ══════════════════════════════════════════════════════════════════════════════
print("[5/7] Integrated power vs pointing …")

fig, axes = plt.subplots(1, 3, figsize=(16, 5), sharey=False)
fig.suptitle("Band-Integrated Power vs Pointing Index", fontweight="bold")

x = np.arange(n_pointings)

for ax, setup in zip(axes, SETUPS):
    freqs = data[setup]["freqs"]
    power = data[setup]["power"]
    for pol_idx, pol_name in enumerate(POL_ORDER):
        integrated = np.nanmean(power[:, pol_idx, :], axis=1)   # mean over freq
        ax.plot(x, integrated,
                color=POL_COLORS[pol_name],
                linestyle=POL_LS[pol_name],
                linewidth=1.2, marker="o", markersize=3,
                label=f"Pol {POL_LABELS[pol_name]}")
    ax.set_title(SETUP_LABELS[setup], fontsize=9)
    ax.set_xlabel("Pointing index")
    ax.set_ylabel("Mean Power (dBm)")
    tick_step = max(1, n_pointings // 8)
    ax.set_xticks(x[::tick_step])
    ax.set_xticklabels(x[::tick_step], rotation=45, ha="right", fontsize=8)
    ax.legend()
    ax.grid(True, alpha=0.3)

save(fig, "5_integrated_power_vs_pointing")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 6 — Polarisation Difference Heatmap (0° − 90°)
# ══════════════════════════════════════════════════════════════════════════════
print("[6/7] Polarisation difference heatmaps …")

fig, axes = plt.subplots(1, 3, figsize=(18, 5))
fig.suptitle("Polarisation Difference (0° − 90°) in dB", fontweight="bold")

for ax, setup in zip(axes, SETUPS):
    freqs = data[setup]["freqs"]
    power = data[setup]["power"]
    diff  = power[:, 0, :] - power[:, 1, :]   # (n_pointings, n_freqs)

    # symmetric colour scale around 0
    vlim = np.nanpercentile(np.abs(diff), 98)

    im = ax.imshow(
        diff,
        aspect="auto",
        origin="lower",
        extent=[freqs[0], freqs[-1], -0.5, n_pointings - 0.5],
        vmin=-vlim, vmax=vlim,
        cmap="RdBu_r",
        interpolation="nearest",
    )
    ax.set_title(SETUP_LABELS[setup], fontsize=9)
    ax.set_xlabel("Frequency (GHz)")
    ax.set_ylabel("Pointing index")

    idxs, labels = pointing_ticks()
    ax.set_yticks(idxs)
    ax.set_yticklabels(labels)

    cb = fig.colorbar(im, ax=ax, shrink=0.85)
    cb.set_label("dPower (dB)")

save(fig, "6_polarisation_difference_heatmap")


# ══════════════════════════════════════════════════════════════════════════════
# CHART 7 — Per-Frequency Power Variance Across Headings
# ══════════════════════════════════════════════════════════════════════════════
print("[7/7] Power variance across headings …")

fig, axes = plt.subplots(1, 3, figsize=(18, 5))
fig.suptitle("Power Std Dev Across Pointing Indices "
             "(high = directional signal or variable RFI)", fontweight="bold")

for ax, setup in zip(axes, SETUPS):
    freqs = data[setup]["freqs"]
    power = data[setup]["power"]
    for pol_idx, pol_name in enumerate(POL_ORDER):
        std_per_freq = np.nanstd(power[:, pol_idx, :], axis=0)
        ax.plot(freqs, std_per_freq,
                color=POL_COLORS[pol_name],
                linestyle=POL_LS[pol_name],
                linewidth=0.8, alpha=0.85,
                label=f"Pol {POL_LABELS[pol_name]}")

    ax.set_title(SETUP_LABELS[setup], fontsize=9)
    ax.set_xlabel("Frequency (GHz)")
    ax.set_ylabel("Std Dev (dB)")
    ax.legend()
    ax.grid(True, alpha=0.3)

save(fig, "7_power_variance_across_headings")


# ══════════════════════════════════════════════════════════════════════════════
# BONUS — Combined power vs heading vs frequency (3-D surface, one per setup)
# ══════════════════════════════════════════════════════════════════════════════
print("[bonus] 3D surface plots …")

from mpl_toolkits.mplot3d import Axes3D   # noqa: F401

for setup in SETUPS:
    freqs = data[setup]["freqs"]
    power = data[setup]["power"]

    # downsample frequency axis to keep rendering fast
    step = max(1, len(freqs) // 200)
    f_ds = freqs[::step]
    x = np.arange(n_pointings)
    F, X = np.meshgrid(f_ds, x)

    fig = plt.figure(figsize=(12, 7))
    for pol_idx, pol_name in enumerate(POL_ORDER):
        ax = fig.add_subplot(1, 2, pol_idx + 1, projection="3d")
        Z  = power[:, pol_idx, ::step]
        surf = ax.plot_surface(F, X, Z, cmap="inferno",
                               linewidth=0, antialiased=False, alpha=0.9)
        ax.set_xlabel("Freq (GHz)", labelpad=6, fontsize=8)
        ax.set_ylabel("Pointing index", labelpad=6, fontsize=8)
        ax.set_zlabel("Power (dBm)", labelpad=6, fontsize=8)
        ax.set_title(f"Pol {POL_LABELS[pol_name]}", fontsize=9)
        fig.colorbar(surf, ax=ax, shrink=0.5, pad=0.1).set_label("dBm", fontsize=8)

    fig.suptitle(f"Power vs Frequency vs Pointing Index — {SETUP_LABELS[setup]}", fontweight="bold")
    slug = setup.replace(" ", "_")
    save(fig, f"bonus_3d_surface_{slug}")

print(f"\nAll done. PNGs saved to:\n  {OUTPUT_DIR}")
