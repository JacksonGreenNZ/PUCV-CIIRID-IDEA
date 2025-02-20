import csv
from skyfield.api import EarthSatellite, load, wgs84, Star, N,W
import numpy as np

def checkOverhead():
    event_names = ['rise above 5°', 'culminate', 'set below 5°']
    satellites_interfere = [] #array to store any satellites that will be 
    #overhead during timeframe
    
    # Iterate through each satellite and check rise, culmination, and fall
    for satellite in sats:

        
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

def checkTargetPosition(t):

    #example target for observation: barnards star:
    barnard = Star(ra_hours=(17, 57, 48.49803), dec_degrees=(4, 41, 36.2072))
    
    astrometric = ssb_warkworth.at(t).observe(barnard)
    apparent = astrometric.apparent()
    
    # #Alt/Az apparent 
    # alt_target, az_target, distance_target = apparent.altaz()
    # print("At ", t.utc_strftime())
    # print("Altitude = ", alt_target.dstr())
    # print("Azimuth = ", az_target.dstr())
    return apparent

def displayTargetPosition(t):

    #example target for observation: barnards star:
    barnard = Star(ra_hours=(17, 57, 48.49803), dec_degrees=(4, 41, 36.2072))
    
    astrometric = ssb_warkworth.at(t).observe(barnard)
    apparent = astrometric.apparent()
    
    #Alt/Az apparent 
    alt_target, az_target, distance_target = apparent.altaz()
    print("At ", t.utc_strftime())
    print("Altitude = ", alt_target.dstr())
    print("Azimuth = ", az_target.dstr())

def timeRange(initialyear, initialmonth, initialday, initialhour, initialminute, initialsecond, endyear, endmonth, endday, endhour, endminute, endsecond):
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
        checkSatelliteIntersect(t_temp)     

def checkSatelliteIntersect(t):
    for satellite in sats:
        difference = satellite - warkworth
        topocentric = difference.at(t)
        alt_sat, az_sat, distance_sat = topocentric.altaz()
        difference_angle = checkTargetPosition(t).separation_from(topocentric)
        threshold_degrees = 5
        if difference_angle.degrees < threshold_degrees:
           print("Satellite {satellite.name} is near the Target")
           print("  - Satellite Alt/Az: {alt_sat.dstr()}, {az_sat.dstr()}")
           print("  - Angular separation: {difference_angle}\n")
    
def main():
    
    global earth
    global warkworth
    global ssb_warkworth
    global ts
    global sats
    
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
    
    warkworth = wgs84.latlon(-36, +174, elevation_m=43)
    ssb_warkworth = earth + warkworth
    
    #checkOverhead() 
    timeRange(2025,1,1,8,0,0, 2025,1,1,8,1,0)

main()

    
