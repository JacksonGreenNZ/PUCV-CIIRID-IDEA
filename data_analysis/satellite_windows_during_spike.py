import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

FWHM = 60.0  # degrees
sigma = FWHM / (2 * np.sqrt(2 * np.log(2)))

sat_file = r"C:\Users\hijox\OneDrive - AUT University\FYP\1-15 First setup.csv-20260123T165606Z-3-001\240 Heading During Spike\satellites.csv" #change depending on file location

# Load satellite data
df = pd.read_csv(sat_file)

# Parse time column
df["Time"] = pd.to_datetime(df["Time"], format="%Y-%m-%d %H:%M:%S UTC")



# UTC windows when heading was aligned with spike

windows = [ ("13:02:08", "13:02:19"), 
           ("13:03:00", "13:03:11"), 
           ("13:03:52", "13:04:03"), 
           ("13:05:34", "13:05:45"), 
           ("13:06:25", "13:06:36"), 
           ("13:08:08", "13:08:19"), ]

date_str = "2026-01-21"

results = []

for i, (start_t, end_t) in enumerate(windows, 1):

    start = pd.to_datetime(f"{date_str} {start_t}")
    end = pd.to_datetime(f"{date_str} {end_t}")

    mask = (df["Time"] >= start) & (df["Time"] <= end)
    window_df = df[mask]
    
    if len(window_df) > 0:

        theta = window_df["Angular Separation"].values

        beam_weights = np.exp(-(theta**2) / (2 * sigma**2))

        weighted_sum = beam_weights.sum()
        weighted_mean_sep = np.average(theta, weights=beam_weights)

    else:
        weighted_sum = 0
        weighted_mean_sep = float("nan")


    sat_count = len(window_df)

    if sat_count > 0:
        mean_sep = window_df["Angular Separation"].mean()
    else:
        mean_sep = float("nan")

    results.append({
    "window": i,
    "start": start,
    "end": end,
    "close_sat_count": len(window_df),
    "beam_weight_sum": weighted_sum,
    "weighted_mean_sep": weighted_mean_sep
})


results_df = pd.DataFrame(results)

# Satellite count per window
plt.figure(figsize=(8,5))
plt.bar(results_df["window"], results_df["close_sat_count"])
plt.xlabel("Time Window Index")
plt.ylabel("Satellite Count")
plt.title("Satellites per Window")
plt.grid(True)
plt.show()


# Beam-weighted mean angular separation
plt.figure(figsize=(8,5))
plt.plot(results_df["window"], results_df["weighted_mean_sep"], marker='o')
plt.xlabel("Time Window Index")
plt.ylabel("Weighted Mean Angular Separation (deg)")
plt.title("Beam Weighted Mean Angular Separation")
plt.grid(True)
plt.show()


# Beam weighted satellite presence
plt.figure(figsize=(8,5))
plt.plot(results_df["window"], results_df["beam_weight_sum"], marker='o')
plt.xlabel("Time Window Index")
plt.ylabel("Beam Weighted Satellite Presence")
plt.title("Beam Weighted Satellite Density (FWHM = 60°)")
plt.grid(True)
plt.show()

plt.figure(figsize=(7,6))

plt.scatter(results_df["weighted_mean_sep"],
            results_df["beam_weight_sum"],
            s=80)

for _, row in results_df.iterrows():
    plt.text(row["weighted_mean_sep"],
             row["beam_weight_sum"],
             f"W{int(row['window'])}",
             fontsize=9,
             ha='right')

plt.xlabel("Beam Weighted Mean Angular Separation (deg)")
plt.ylabel("Beam Weighted Satellite Presence")
plt.title("Beam Weighted Separation vs Satellite Presence")
plt.grid(True)
plt.show()
