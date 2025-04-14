import csv
from skyfield.api import EarthSatellite, load, wgs84, Star
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from tqdm import tqdm
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

#TO DO
#add to get user input for angular resolution 1.22*(wavelength/lens diameter)*SF for the interference angle.  
#for optical telescopes 350-700 nanometre wavelength, for radio telescopes it's 0.001m to 10m wavelength. 
#option for selecting telescope type? (radio/optical)

#satellite class for plotting flight path easier
class Satellite:
    def __init__(self, name):
        self.name = name
        self.times = []  #list of datetime objects
        self.alts = []  
        self.azs = []  

    def add_position(self, time, alt, az):
        self.times.append(time)
        self.alts.append(alt)
        self.azs.append(az)

#load earth data from skyfield, timescale, beamwidth 
planets = load('de421.bsp')
earth = planets['earth']
ts = load.timescale()

beamwidth = 1.4

#ensure variables can be imported  (for later gui implementation)
__all__ = [
    "sat_track_plot", "select_data", "precompute_target_positions", 
    "precompute_satellite_positions", "check_satellite_intersect", "earth", "ts"
]

def select_data(type):
    max_days = 7.0         #download again once 7 days old
    name = f'{type}.csv'   #custom filename based on type
    
    base = 'https://celestrak.org/NORAD/elements/gp.php'
    url = f'{base}?GROUP={type}&FORMAT=csv'  #dynamically insert type
    
    if not load.exists(name) or load.days_old(name) >= max_days:
        load.download(url, filename=name)
    
    with load.open(name, mode='r') as f:
        data = list(csv.DictReader(f))
        
    sats = [EarthSatellite.from_omm(ts, fields) for fields in data]
    print('Loaded', len(sats), 'satellites')
    return sats

    #load satellite data
sats = select_data("active")

def precompute_target_positions(target, time_steps, observerSSB): 
    return observerSSB.at(time_steps).observe(target).apparent()#returns apparent position - check if this is correct or not. Radio interference isn't as significant as optical.

def precompute_satellite_positions(sats, time_steps, observer):
    return {sat: (sat - observer).at(time_steps) for sat in sats}

def check_satellite_intersect(t_index, targPos, sat_positions):
    intersecting_sats = []
    
    #loop through sat positions at a certain time and check if it's near target
    for sat, topocentric in sat_positions.items():
        difference_angle = targPos.separation_from(topocentric[t_index])
        

        if difference_angle.degrees < beamwidth: #adjusted to match the rayleigh criterion, 2 sigma
            intersecting_sats.append((sat, topocentric[t_index], difference_angle))
    
    return intersecting_sats

def sat_track_plot(target, observer, t_init, t_end, sats):
    #Lists for plotting
    times, alts, azs = [], [], []
    sat_times, sat_alts, sat_azs = [], [], []

    #List for CSV export
    output_data = []

    one_second = np.float64(0.00001157407) #skyfield time maths sets 1 day = 1
    time_steps = ts.tt_jd(np.arange(t_init.tt, t_end.tt, one_second))  #vectorised time steps to save compute time
    total_steps = len(time_steps)


    #determine positions before checking angle difference - faster
    observerSSB = observer+earth
    precomputed_positions = precompute_target_positions(target, time_steps, observerSSB)
    precomputed_sat_positions = precompute_satellite_positions(sats, time_steps, observer)
    
    satellites = [] #initialise a list of satellite objects

    with tqdm(total=total_steps, desc="Processing", unit="step") as pbar:#creates a progress bar - observations can be long
        for i, t_temp in enumerate(time_steps):
            apparent = precomputed_positions[i]  #Use precomputed data
            alt, az, _ = apparent.altaz()

            #store target position for plotting
            times.append(t_temp.utc_datetime())
            alts.append(alt.degrees)
            azs.append(az.degrees)

            #add target data for CSV output
            output_data.append([t_temp.utc_strftime(), "Target", alt.degrees, az.degrees, "-"])
            
            #check for satellite intersections
            sat_intersects = check_satellite_intersect(i, apparent, precomputed_sat_positions)
            for sat, topocentric, difference_angle in sat_intersects:
                sat_alt, sat_az, _ = topocentric.altaz()

                #add satellite data to the relevant satellite object
                sat_obj = next((s for s in satellites if s.name == sat.name), None)
                if sat_obj is None:
                    sat_obj = Satellite(name=sat.name)
                    satellites.append(sat_obj)
                
                sat_obj.add_position(t_temp.utc_datetime(), sat_alt.degrees, sat_az.degrees)

                #add satellite data for CSV output
                output_data.append([
                    t_temp.utc_strftime(),
                    sat.name,
                    sat_alt.degrees,
                    sat_az.degrees,
                    difference_angle.degrees
                ])
            pbar.update(1)  #update progress bar         

    #save data to CSV file
    local_time = datetime.now()
    timestamp = local_time.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"sat_intersect_{timestamp}.csv"

    with open(filename, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["Time", "Object", "Altitude", "Azimuth", "Angular Separation"])
        writer.writerows(output_data)

    print(f"Saved satellite and target position data to {filename}")

    #plot
    fig3d, fig2d, anim = create_visualisation(times, alts, azs, satellites)
    plt.show()
    
def create_visualisation(times, alts, azs, satellites):
    
    #create 3d plot with target position
    fig1 = plt.figure(figsize=(18, 12))
    ax1 = fig1.add_subplot(111, projection='3d')
    time_nums = np.array([(t - times[0]).total_seconds() for t in times])
    ax1.scatter(time_nums, azs, alts, label="Target Path", c='b', marker='o', s=10)

    #plot satellites with flight path drawn
    for sat in satellites:
        sat_time_nums = np.array([(t - times[0]).total_seconds() for t in sat.times])
        ax1.plot(sat_time_nums, sat.azs, sat.alts, label=f"{sat.name} Path", linestyle='-', linewidth=2)

    #graph data/layout
    ax1.set_xlabel("Time (seconds)")
    ax1.set_ylabel("Azimuth (degrees)")
    ax1.set_zlabel("Altitude (degrees)")
    ax1.grid(True, linestyle="--", alpha=0.6)
    ax1.legend()
    fig1.tight_layout()
    plt.show()

    #animated plot
    fig2, ax2 = plt.subplots(figsize=(10, 8))
    
    #use dictionary to organise data by time
    time_organised_data = {}
    for i, t in enumerate(times):
        time_key = t.strftime("%Y-%m-%d %H:%M:%S")
        if time_key not in time_organised_data:
            time_organised_data[time_key] = []
        time_organised_data[time_key].append({
            'name': 'Target',
            'alt': alts[i],
            'az': azs[i]
        })
    
    #sdd satellite data
    for sat in satellites:
        for i, t in enumerate(sat.times):
            time_key = t.strftime("%Y-%m-%d %H:%M:%S")
            if time_key not in time_organised_data:
                time_organised_data[time_key] = []
            time_organised_data[time_key].append({
                'name': sat.name,
                'alt': sat.alts[i],
                'az': sat.azs[i]
            })
    
    #sort times
    sorted_times = list(sorted(time_organised_data.keys()))
    
    #initialise plot
    target_point, = ax2.plot([], [], 'bo', markersize=8, label='Target')
    target_trajectory_x = []
    target_trajectory_y = []
    target_traj_line, = ax2.plot([], [], 'b-', alpha=0.3)
    
    #create satellite markers dynamically
    sat_markers = []
    sat_labels = []
    
    #set up plot
    ax2.set_title('Target Position (Altitude vs Azimuth)', fontsize=16)
    ax2.set_xlabel('Azimuth (degrees)', fontsize=12)
    ax2.set_ylabel('Altitude (degrees)', fontsize=12)
    ax2.set_xlim(min(azs)-(beamwidth*1.05), max(azs)+(beamwidth*1.05))#zoom in on the target based on beamwidth
    ax2.set_ylim(min(alts)-(beamwidth*1.05), max(alts)+(beamwidth*1.05))
    ax2.grid(True)
    ax2.legend()
    
    def init():
        target_point.set_data([], [])
        target_traj_line.set_data([], [])
        return [target_point, target_traj_line]
    
    def animate(i):
        time_key = sorted_times[i % len(sorted_times)]
        
        #clear previous satellite markers and labels
        for marker in sat_markers[:]:
            marker.remove()
            sat_markers.remove(marker)
        
        for label in sat_labels[:]:
            label.remove()
            sat_labels.remove(label)
        
        current_objects = time_organised_data[time_key]
        
        for obj in current_objects:
            if obj['name'] == 'Target':
                #update target position
                x = obj['az']
                y = obj['alt']
                target_point.set_data([x], [y])
                #update target trajectory
                target_trajectory_x.append(x)
                target_trajectory_y.append(y)
                target_traj_line.set_data(target_trajectory_x, target_trajectory_y)
            else:
                #add satellite marker
                marker, = ax2.plot([obj['az']], [obj['alt']], 'rx', markersize=10)
                label = ax2.annotate(obj['name'], xy=(obj['az'], obj['alt']), 
                                    xytext=(5, 5), textcoords='offset points',
                                    fontsize=9, color='red')
                sat_markers.append(marker)
                sat_labels.append(label)
        
        ax2.set_title(f'Target Position - {time_key}', fontsize=16)
        
        return [target_point, target_traj_line] + sat_markers + sat_labels
    
    #display
    animation = FuncAnimation(
        fig2, animate, init_func=init, frames=len(sorted_times), interval=10, blit=False
    )
    
    return fig1, fig2, animation

def get_observation_data():
    #testing mode or not
    testing_choice = input("Testing? (y/n): ").strip().lower()

    if testing_choice == "y":
        #sse predefined values for testing
        year, month, day, hour, minute, duration = 2025, 10, 10, 13, 30, 5
        target = Star(ra_hours=(8, 35, 20.65525), dec_degrees=(-45, 10, 35.1545))  #Vela
        observer = wgs84.latlon(-36, +174, elevation_m=64)  #Warkworth observer
    else:
        #normal input flow for non-testing
        year = int(input("Enter year (YYYY): "))
        month = int(input("Enter month (MM): "))
        day = int(input("Enter day (DD): "))
        hour = int(input("Enter hour (HH, UTC): "))
        minute = int(input("Enter minute (MM, UTC): "))
        duration = int(input("Enter observation duration in minutes: "))

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
    #get user inputs
    year, month, day, hour, minute, duration, target, observer = get_observation_data()

    #define time range
    start_time = ts.utc(year, month, day, hour, minute)
    end_time = ts.utc(year, month, day, hour, minute + duration) 
    
    #run interference checker/plotter
    sat_track_plot(target, observer, start_time, end_time, sats)

if __name__ == "__main__":
    main()
