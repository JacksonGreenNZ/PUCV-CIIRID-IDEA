import csv
from skyfield.api import EarthSatellite, load, wgs84, Star, N,W
import numpy as np

planets = load('de421.bsp')
earth = planets['earth']

#loading stations only to limit computation

max_days = 7.0         # download again once 7 days old
name = 'stations.csv'  # custom filename, not 'gp.php'

base = 'https://celestrak.org/NORAD/elements/gp.php'
url = base + '?GROUP=stations&FORMAT=csv'

if not load.exists(name) or load.days_old(name) >= max_days:
    load.download(url, filename=name)

with load.open('stations.csv', mode='r') as f:
    data = list(csv.DictReader(f))

ts = load.timescale()
sats = [EarthSatellite.from_omm(ts, fields) for fields in data]
print('Loaded', len(sats), 'satellites')

def check_overhead():
    # Event names
    event_names = ['rise above 5°', 'culminate', 'set below 5°']
    satellites_interfere = [] #array to store any satellites that will be 
    #overhead during timeframe
    
    # Iterate through each satellite and check rise, culmination, and fall
    for satellite in sats:
        
        warkworth = wgs84.latlon(-36, +174)
        
        t0 = ts.utc(2025, 1, 1, 8)
        t1 = ts.utc(2025, 1, 1, 14)
        
        t, events = satellite.find_events(warkworth, t0, t1, altitude_degrees=5.0)
    
        # If no events (rise or set), skip this satellite
        if len(events) == 0:
            continue    
    
        #print satellite so we know what info we have
        satellite_name = satellite.name
        print(f"Processing satellite: {satellite_name}")
    
        satellites_interfere.append(satellite.name)#add to list
        
        for ti, event in zip(t, events):
            name = event_names[event]
            print(ti.utc_strftime('%Y %b %d %H:%M:%S'), name)
            
    print(satellites_interfere)

#The main factor in tracking a distant object is earth rotation, not object 
#movement, so if we pick a spot and track it throughout time, then
#crossreference with the satellites that rise or fall and their position at 
#each time, we can determine interference. 

# EVERYTHING ABOVE THIS WORKS

def check_target_position(t):

    #example target for observation: barnards star:
    barnard = Star(ra_hours=(17, 57, 48.49803), dec_degrees=(4, 41, 36.2072))
    
    warkworth = earth + wgs84.latlon(-36 * N, 174 * W, elevation_m=43)
    
    astrometric = warkworth.at(t).observe(barnard)
    apparent = astrometric.apparent()
    
    #ra, dec
    ra, dec, distance = astrometric.radec()
    
    #ra, dec apparent
    ra, dec, distance = apparent.radec('date')
    
    #Alt/Az apparent 
    alt, az, distance = apparent.altaz()
    print("At ", t.utc_strftime())
    print("Altitude = ", alt.dstr())
    print("Azimuth = ", az.dstr())

def timerange(initialyear, initialmonth, initialday, initialhour, initialminute, initialsecond, endyear, endmonth, endday, endhour, endminute, endsecond):
    times=[]
    t_init = ts.utc(initialyear, initialmonth, initialday, initialhour, initialminute, initialsecond)
    t_end = ts.utc(endyear, endmonth, endday, endhour, endminute, endsecond)
    t_dif = t_end-t_init
    one_second = np.float64(0.00001157407)
    steps = int(t_dif/one_second)
    print('Seconds: ',steps)
    t_temp = t_init
    times.append(t_init)
    for i in range(steps):
        t_temp = t_temp+one_second
        times.append(t_temp)
    for x in times:
        check_target_position(x)

def main():
    check_overhead() 
    timerange(2025,1,1,8,0,0, 2025,1,1,8,1,0)

main()



#EVERYTHING ABOVE THIS WORKS

""" NOT WORKING
line1 = '1 25544U 98067A   14020.93268519  .00009878  00000-0  18200-3 0  5082'
line2 = '2 25544  51.6498 109.4756 0003572  55.9686 274.8005 15.49815350868473'
satellite = EarthSatellite(line1, line2, 'ISS (ZARYA)', ts)

warkworth2 = earth + Topos(latitude_degrees=-36, longitude_degrees=174, elevation_m=43)

# Compute the satellite's position at the same time t
satellite_position = satellite.at(t)

# Compute the observer's position at time t
observer_position = warkworth.at(t)

# Compute the difference (relative position between satellite and observer)
difference = satellite_position - observer_position

topocentric = difference.at(t)
print(topocentric.position.km)
alt, az, distance = topocentric.altaz()

if alt.degrees > 0:
    print('The ISS is above the horizon')
    print('Altitude:', alt)
    print('Azimuth:', az)
"""


    
