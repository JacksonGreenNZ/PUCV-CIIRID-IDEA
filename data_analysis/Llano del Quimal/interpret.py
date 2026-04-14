import re
import numpy as np
import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).parent
SETUPS = ["first setup", "second setup", "third setup"]

AZ0_DEG = 0.0
DAZ_DEG = 2.0

POL_ORDER = ["0deg", "90deg"]
REPEATS_PER_POL = 1
# =========================

def setup_id_from_csv(df: pd.DataFrame):
    fmin = df["frequency_Hz"].min() / 1e9
    fmax = df["frequency_Hz"].max() / 1e9
    return f"{fmin:.3f}-{fmax:.3f}GHz"

def parse_timestamp_from_name(stem: str):
    # pattern: EOSYYYYMMDDHHMMSSmmm
    m = re.search(r"(?:EOS)?(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})(\d{3})", stem)
    if not m:
        return pd.NaT
    y, mo, d, hh, mi, ss, ms = map(int, m.groups())
    t = pd.Timestamp(year=y, month=mo, day=d, hour=hh, minute=mi, second=ss)
    return t + pd.Timedelta(milliseconds=ms)

def assign_pol_pointing(g: pd.DataFrame) -> pd.DataFrame:
    g = g.sort_values(["timestamp", "file"], na_position="last").reset_index(drop=True)
    block = REPEATS_PER_POL * len(POL_ORDER)
    i = np.arange(len(g))

    g["pol"] = [POL_ORDER[(k // REPEATS_PER_POL) % len(POL_ORDER)] for k in i]
    g["pointing_idx"] = i // block
    g["az_deg"] = (AZ0_DEG + g["pointing_idx"] * DAZ_DEG) % 360.0
    return g

def process_setup(setup_name: str) -> tuple[pd.DataFrame, list]:
    csv_dir = BASE_DIR / setup_name
    csv_files = sorted(csv_dir.glob("EOS*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No EOS*.csv files found in {csv_dir}")

    rows = []
    skipped = []

    for p in csv_files:
        df = pd.read_csv(p)
        if {"frequency_Hz", "power_dBm"}.issubset(df.columns):
            rows.append({
                "file": f"{p.parent.name}/{p.name}",
                "timestamp": parse_timestamp_from_name(p.stem),
                "setup_id": setup_id_from_csv(df),
            })
        else:
            skipped.append(p.name)

    index = pd.DataFrame(rows).sort_values(["setup_id", "timestamp", "file"], na_position="last").reset_index(drop=True)
    index = index.groupby("setup_id", group_keys=False).apply(assign_pol_pointing)
    return index, skipped

all_frames = []
all_skipped = []

for setup in SETUPS:
    print(f"\n--- {setup} ---")
    index, skipped = process_setup(setup)
    print(f"Valid spectra: {len(index)}")
    if skipped:
        print(f"Skipped: {len(skipped)}")
    all_frames.append(index)
    all_skipped.extend(skipped)

combined = pd.concat(all_frames, ignore_index=True)

print(f"\n=== Combined ({len(combined)} total spectra) ===")
if all_skipped:
    print(f"Total skipped: {len(all_skipped)}")
print(combined.to_string())
