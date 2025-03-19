import csv
from skyfield.api import EarthSatellite, load, wgs84, Star
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import pytz
from tqdm import tqdm

#load earth data, timescale, satellite 
planets = load('de421.bsp')
earth = planets['earth']
ts = load.timescale()

    #ensure variables can be imported
__all__ = [
    "satTrackPlot", "selectData", "precomputeTargetPositions", 
    "precomputeSatellitePositions", "checkSatelliteIntersect", "earth", "ts"
]

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

    #load satellite data
sats = selectData("active")

def precomputeTargetPositions(target, time_steps, observerSSB): 
    return observerSSB.at(time_steps).observe(target).apparent()

def precomputeSatellitePositions(sats, time_steps, observer):
    return {sat: (sat - observer).at(time_steps) for sat in sats}

def checkSatelliteIntersect(t_index, targPos, sat_positions):
    intersecting_sats = []
    
    for sat, topocentric in sat_positions.items():
        difference_angle = targPos.separation_from(topocentric[t_index])
        
        if difference_angle.degrees < 1.4: #adjusted to match the rayleigh criterion, 2 sigma
            intersecting_sats.append((sat, topocentric[t_index], difference_angle))
    
    return intersecting_sats

def satTrackPlot(target, observer, t_init, t_end, sats):
    # Lists for plotting
    times, alts, azs = [], [], []
    sat_times, sat_alts, sat_azs = [], [], []

    # List for CSV export
    output_data = []

    one_second = np.float64(0.00001157407)
    time_steps = ts.tt_jd(np.arange(t_init.tt, t_end.tt, one_second))  # vectorised time steps to save compute time
    total_steps = len(time_steps)


    # determine positions before checking angle difference
    observerSSB = observer+earth
    precomputed_positions = precomputeTargetPositions(target, time_steps, observerSSB)
    precomputed_sat_positions = precomputeSatellitePositions(sats, time_steps, observer)

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



def get_user_inputs():
    # Get date and observation duration
    year = int(input("Enter year (YYYY): "))
    month = int(input("Enter month (MM): "))
    day = int(input("Enter day (DD): "))
    hour = int(input("Enter hour (HH, UTC): "))
    minute = int(input("Enter minute (MM, UTC): "))
    duration = int(input("Enter observation duration in minutes: "))

    # Get target
    target_choice = input("Enter target (vela/custom): ").strip().lower()
    if target_choice == "vela":
        target = Star(ra_hours=(8, 35, 20.65525), dec_degrees=(-45, 10, 35.1545))
    else:
        ra_h = float(input("Enter RA (hours): "))
        ra_m = float(input("Enter RA (minutes): "))
        ra_s = float(input("Enter RA (seconds): "))
        dec_d = float(input("Enter Dec (degrees): "))
        dec_m = float(input("Enter Dec (arcminutes): "))
        dec_s = float(input("Enter Dec (arcseconds): "))
        target = Star(ra_hours=(ra_h, ra_m, ra_s), dec_degrees=(dec_d, dec_m, dec_s))
    
    # Get observer location
    location_choice = input("Enter observer location (warkworth/custom): ").strip().lower()
    if location_choice == "warkworth":
        observer = wgs84.latlon(-36, +174, elevation_m=128)
    else:
        lat = float(input("Enter latitude: "))
        lon = float(input("Enter longitude: "))
        elevation = float(input("Enter elevation (m): "))
        observer = wgs84.latlon(lat, lon, elevation_m=elevation)
    
    return year, month, day, hour, minute, duration, target, observer   

def main():
    # Get user inputs
    year, month, day, hour, minute, duration, target, observer = get_user_inputs()

    # Define time range
    start_time = ts.utc(year, month, day, hour, minute)
    end_time = ts.utc(year, month, day, hour, minute + duration) 
    
    #run interference checker
    satTrackPlot(target, observer, start_time, end_time, sats)

if __name__ == "__main__":
    main()
