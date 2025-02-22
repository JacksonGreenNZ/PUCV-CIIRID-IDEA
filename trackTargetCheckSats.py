import csv
from skyfield.api import EarthSatellite, load, wgs84, Star
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import pytz
from tqdm import tqdm

# Precomupte target and sat positions with Time object array instead of individual time objects (3.3x speed improvement)

def precomputeTargetPositions(target, time_steps): 
    return ssb_warkworth.at(time_steps).observe(target).apparent()

def precomputeSatellitePositions(sats, time_steps):
    return {sat: (sat - warkworth).at(time_steps) for sat in sats}

def checkSatelliteIntersect(t_index, targPos, sat_positions):
    intersecting_sats = []
    
    for sat, topocentric in sat_positions.items():
        difference_angle = targPos.separation_from(topocentric[t_index])
        
        if difference_angle.degrees < 1.5:
            intersecting_sats.append((sat, topocentric[t_index], difference_angle))
    
    return intersecting_sats

def satTrackPlot(target, t_init, t_end):
    # Lists for plotting
    times, alts, azs = [], [], []
    sat_times, sat_alts, sat_azs = [], [], []

    # List for CSV export
    output_data = []

    one_second = np.float64(0.00001157407)
    time_steps = ts.tt_jd(np.arange(t_init.tt, t_end.tt, one_second))  # vectorised time steps to save compute time
    total_steps = len(time_steps)

    # determine positions before checking angle difference
    precomputed_positions = precomputeTargetPositions(target, time_steps)
    precomputed_sat_positions = precomputeSatellitePositions(sats, time_steps)

    with tqdm(total=total_steps, desc="Processing", unit="step") as pbar: #initialises a progress bar
        for i, t_temp in enumerate(time_steps):
            apparent = precomputed_positions[i]  # Use precomputed value
            alt, az, _ = apparent.altaz()

            # Store target position for plotting
            times.append(t_temp.utc_datetime())
            alts.append(alt.degrees)
            azs.append(az.degrees)

            # Store target position in CSV
            output_data.append([t_temp.utc_strftime(), "Target", alt.degrees, az.degrees, "-"])

            # Check for satellite intersections
            sat_intersects = checkSatelliteIntersect(i, apparent, precomputed_sat_positions)
            for sat, topocentric, difference_angle in sat_intersects:
                sat_alt, sat_az, _ = topocentric.altaz()

                # Store satellite position for plotting
                sat_times.append(t_temp.utc_datetime())
                sat_alts.append(sat_alt.degrees)
                sat_azs.append(sat_az.degrees)

                # Store satellite data in CSV
                output_data.append([
                    t_temp.utc_strftime(),
                    sat.name,
                    sat_alt.degrees,
                    sat_az.degrees,
                    difference_angle.degrees
                ])
            pbar.update(1)  # Update progress bar            

    # Save data to CSV file
    nz_time = datetime.now(pytz.timezone("Pacific/Auckland"))
    timestamp = nz_time.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"sat_intersect_{timestamp}.csv"

    with open(filename, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Time", "Object", "Altitude", "Azimuth", "Angular Separation"])
        writer.writerows(output_data)

    print(f"Saved satellite and target position data to {filename}")

    # Plot the data
    plot_3d(times, alts, azs, sat_times, sat_alts, sat_azs)

def plot_3d(times, alts, azs, sat_times, sat_alts, sat_azs):
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')

    # Convert time to numerical values relative to start
    time_nums = np.array([(t - times[0]).total_seconds() for t in times])
    sat_time_nums = np.array([(t - times[0]).total_seconds() for t in sat_times])

    # Plot target movement
    ax.scatter(time_nums, azs, alts, label="Target Path", c='b', marker='o', s=10)

    # Plot satellites if any were found
    if sat_times:
        ax.scatter(sat_time_nums, sat_azs, sat_alts, label="Satellites", c='r', marker='x', s=30)

    # Labels and viewing angle
    ax.set_xlabel("Time")
    ax.set_ylabel("Azimuth (degrees)")
    ax.set_zlabel("Altitude (degrees)")
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend()

    # Set axis limits
    #ax.set_ylim(0, 360)  # Azimuth range
    #ax.set_zlim(0, 90)   # Altitude range

    plt.show()

def selectData(type):
    max_days = 7.0         # download again once 7 days old
    name = f'{type}.csv'   # custom filename based on type
    
    base = 'https://celestrak.org/NORAD/elements/gp.php'
    url = f'{base}?GROUP={type}&FORMAT=csv'  # dynamically insert type
    
    if not load.exists(name) or load.days_old(name) >= max_days:
        load.download(url, filename=name)
    
    with load.open(name, mode='r') as f:
        data = list(csv.DictReader(f))
        
    sats = [EarthSatellite.from_omm(ts, fields) for fields in data]
    print('Loaded', len(sats), 'satellites')
    return sats



def main():
    global earth, warkworth, ssb_warkworth, ts, sats     #used in multiple functions

    #load earth data, timescale, satellite 
    planets = load('de421.bsp')
    earth = planets['earth']
    ts = load.timescale()

    #load satellite data, defined observe position (local and solar system baryonic) 
    sats = selectData("starlink")
    warkworth = wgs84.latlon(-36, +174, elevation_m=43)
    ssb_warkworth = earth + warkworth

    #define target and time range
    vela = Star(ra_hours=(8,35,20.65525), dec_degrees=(-45, 10, 35.1545))
    startTime = ts.utc(2025,1,1,8,0,0)
    endTime = ts.utc(2025,1,1,8,5,0)
    
    #run interference checker
    satTrackPlot(vela, startTime, endTime)

main()
