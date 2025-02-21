import csv
from skyfield.api import EarthSatellite, load, wgs84, Star
import numpy as np
import matplotlib.pyplot as plt

def checkTargetPosition(t, target):
    astrometric = ssb_warkworth.at(t).observe(target)
    return astrometric.apparent()

def timeRange(target, t_init, t_end):
    times, alts, azs = [], [], []
    sat_times, sat_alts, sat_azs, sat_names = [], [], [], []

    one_second = np.float64(0.00001157407)
    t_temp = t_init

    while t_temp.tt <= t_end.tt:
        apparent = checkTargetPosition(t_temp, target)
        alt, az, _ = apparent.altaz()
        
        times.append(t_temp.utc_datetime())
        alts.append(alt.degrees)
        azs.append(az.degrees)

        # Print target position
        print(f"At {t_temp.utc_strftime()}:")
        print(f"Alt: {alt.degrees:.2f}°")
        print(f"Az: {az.degrees:.2f}°") 

        # Check for satellite intersections
        sat_intersects = checkSatelliteIntersect(t_temp, apparent)
        for sat, topocentric, difference_angle in sat_intersects:
            sat_alt, sat_az, _ = topocentric.altaz()
            
            # Store for plotting
            sat_times.append(t_temp.utc_datetime())
            sat_alts.append(sat_alt.degrees)
            sat_azs.append(sat_az.degrees)
            sat_names.append(sat.name)

            # Print satellite info
            print(f"Satellite {sat.name} is near the Target")
            print(f"  - Satellite Alt/Az: {sat_alt.dstr()}, {sat_az.dstr()}")
            print(f"  - Angular separation: {difference_angle.degrees:.2f}°\n")

        t_temp += one_second  # Increment by one second

    # Plot both target and satellites
    plot_3d(times, alts, azs, sat_times, sat_alts, sat_azs)


def checkSatelliteIntersect(t, targPos):
    intersecting_sats = []
    
    for satellite in sats:
        difference = satellite - warkworth
        topocentric = difference.at(t)
        difference_angle = targPos.separation_from(topocentric)

        threshold_degrees = 2  # arbitrarily chosen
        if difference_angle.degrees < threshold_degrees:
            intersecting_sats.append((satellite, topocentric, difference_angle))

    return intersecting_sats  # Return satellite name and position data for any that come within threshold


def plot_3d(times, alts, azs, sat_times, sat_alts, sat_azs):
    fig = plt.figure(figsize=(10, 7))
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
    global earth, warkworth, ssb_warkworth, ts, sats

    planets = load('de421.bsp')
    earth = planets['earth']
    
    ts = load.timescale()
    sats = selectData("starlink")

    warkworth = wgs84.latlon(-36, +174, elevation_m=43)
    ssb_warkworth = earth + warkworth
    
    vela = Star(ra_hours=(8,35,20.65525), dec_degrees=(-45, 10, 35.1545))
    
    timeRange(vela, ts.utc(2025,1,1,8,0,0), ts.utc(2025,1,1,8,1,0))

main()
