import pandas as pd
import matplotlib.pyplot as plt
import glob
import os
import re
from datetime import datetime
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

pol0_map = {}
pol90_map = {}
freq_axis = None

def extract_timestamp(filename):
    # Example: EOS20250101123015999.csv
    match = re.search(r"EOS(\d{17})", filename)
    if not match:
        raise ValueError(f"Invalid filename format: {filename}")
    return datetime.strptime(match.group(1), "%Y%m%d%H%M%S%f")

data_folder = r"C:\Users\hijox\OneDrive - AUT University\FYP\1-15 First setup.csv-20260123T165606Z-3-001\1-15 First setup.csv"

files = glob.glob(os.path.join(data_folder, "EOS*.csv"))

files_sorted = sorted(files, key=extract_timestamp)

print("Total files found:", len(files_sorted))

azimuths = list(range(0, 360, 30))
azimuths = azimuths[:1] + azimuths[:0:-1]  # reorder to 0,330,300,...,30

polarisations = [0, 90]

group_size = 3

results = []

file_index = 0

files_240 = []

for az in azimuths:
    for pol in polarisations:

        group_files = files_sorted[file_index:file_index + group_size]
        file_index += group_size
        
        if az == 240:
            files_240.extend(group_files)

        dfs = []

        for f in group_files:
            df = pd.read_csv(
                f,
                header=None,
                skiprows=1,
                engine="python",
                sep=None
            )

            df = df.iloc[:, :2]

            if df.shape[1] != 2:
                raise ValueError(f"File has unexpected format: {f}")

            df.columns = ["frequency_Hz", "power_dBm"]

            dfs.append(df)

        merged = dfs[0][["frequency_Hz"]].copy()

        for i, df in enumerate(dfs):
            merged[f"p{i}"] = df["power_dBm"].values

        merged["mean_power_freq"] = merged[[f"p{i}" for i in range(group_size)]].mean(axis=1)
        if freq_axis is None:
            freq_axis = merged["frequency_Hz"].values

        if pol == 0:
            pol0_map[az] = merged["mean_power_freq"].values
        else:
            pol90_map[az] = merged["mean_power_freq"].values


        # Average across frequency bins
        overall_mean_power = merged["mean_power_freq"].mean()

        results.append({
            "azimuth": az,
            "polarisation": pol,
            "avg_power_dBm": overall_mean_power
        })


#checking spike locations
target_az = 240

az_index = azimuths.index(target_az)

files_per_az = len(polarisations) * group_size  # 2 * 3 = 6

start_idx = az_index * files_per_az
end_idx = start_idx + files_per_az

files_240 = files_sorted[start_idx:end_idx]

print("Files for 240°:")
for f in files_240:
    print(os.path.basename(f))
#end


results_df = pd.DataFrame(results)

pol0 = results_df[results_df["polarisation"] == 0].sort_values("azimuth")
pol90 = results_df[results_df["polarisation"] == 90].sort_values("azimuth")

diff_power = pol0["avg_power_dBm"].values - pol90["avg_power_dBm"].values
az = pol0["azimuth"].values


plt.figure(figsize=(8, 5))
plt.plot(pol0["azimuth"], pol0["avg_power_dBm"], marker='o')
plt.xlabel("Azimuth (degrees)")
plt.ylabel("Average Power (dBm)")
plt.title("Average Power vs Azimuth (Polarisation 0°)")
plt.grid(True)
plt.show()

plt.figure(figsize=(8, 5))
plt.plot(pol90["azimuth"], pol90["avg_power_dBm"], marker='o')
plt.xlabel("Azimuth (degrees)")
plt.ylabel("Average Power (dBm)")
plt.title("Average Power vs Azimuth (Polarisation 90°)")
plt.grid(True)
plt.show()

plt.figure(figsize=(8, 5))
plt.plot(az, diff_power, marker='o')
plt.xlabel("Azimuth (degrees)")
plt.ylabel("Power Difference (dB)")
plt.title("Polarisation Difference (0° − 90°)")
plt.grid(True)
plt.show()

fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection="3d")

# Plot polarisation 0°
for az in sorted(pol0_map.keys()):
    az_array = np.full_like(freq_axis, az)
    ax.plot(freq_axis, az_array, pol0_map[az])

# Plot polarisation 90°
for az in sorted(pol90_map.keys()):
    az_array = np.full_like(freq_axis, az)
    ax.plot(freq_axis, az_array, pol90_map[az], linestyle="dashed")

ax.set_xlabel("Frequency (Hz * 10^10)")
ax.set_ylabel("Azimuth (degrees)")
ax.set_zlabel("Power (dBm)")

ax.set_title("Power vs Frequency and Azimuth (Solid = Pol 0°, Dashed = Pol 90°)")

plt.show()

plt.figure(figsize=(9, 6))

max_power = 0
for f in files_240:

    df = pd.read_csv(
        f,
        header=None,
        skiprows=1,
        engine="python",
        sep=None
    )

    df = df.iloc[:, :2]
    df.columns = ["frequency_Hz", "power_dBm"]

    freq_ghz = df["frequency_Hz"].values / 1e9
    power = df["power_dBm"].values

    label = os.path.basename(f)

    plt.plot(freq_ghz, power, label=label)
    # Track maximum
    local_max_idx = power.argmax()
    local_max_power = power[local_max_idx]

    if local_max_power > max_power:
        max_power = local_max_power
        max_freq = freq_ghz[local_max_idx]
        max_file = label

plt.scatter(max_freq, max_power, s=80)
annotation_text = (
    f"Max Power: {max_power:.2f} dBm\n"
    f"Freq: {max_freq:.3f} GHz\n"
    f"File: {max_file}"
)

plt.annotate(
    annotation_text,
    xy=(max_freq, max_power),
    xytext=(-10, -10),
    textcoords="offset points",
    arrowprops=dict(arrowstyle="->")
)

plt.xlabel("Frequency (GHz)")
plt.ylabel("Power (dBm)")
plt.title("All Measurements at Azimuth 240°")
plt.grid(True)
plt.legend(fontsize=7)
plt.show()

