import csv
from skyfield.api import EarthSatellite, load, wgs84, Star
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

def checkTargetPosition(t, target):
    
    astrometric = ssb_warkworth.at(t).observe(target)
    apparent = astrometric.apparent()
    
    return apparent

def displayTargetPosition(t, target):
    
    astrometric = ssb_warkworth.at(t).observe(target)
    apparent = astrometric.apparent()
    
    #Alt/Az apparent 
    alt_target, az_target, distance_target = apparent.altaz()
    print("At ", t.utc_strftime())
    print("Altitude = ", alt_target.dstr())
    print("Azimuth = ", az_target.dstr())

def timeRange(target, t_init, t_end):
    times=[]
    t_dif = t_end-t_init
    one_second = np.float64(0.00001157407)
    steps = int(t_dif/one_second)
    print('Seconds: ',steps)
    t_temp = t_init
    times.append(t_init)
    for i in range(steps):
        t_temp = t_temp+one_second
        times.append(t_temp)
        checkSatelliteIntersect(t_temp, target)
        displayTargetPosition(t_temp, target)

def checkSatelliteIntersect(t, target):
    targPos = checkTargetPosition(t, target)
    for satellite in sats:
        difference = satellite - warkworth
        topocentric = difference.at(t)
        alt_sat, az_sat, distance_sat = topocentric.altaz()
        difference_angle = targPos.separation_from(topocentric)
        threshold_degrees = 2
        if difference_angle.degrees < threshold_degrees:
           print(f"Satellite {satellite.name} is near the Target")
           print(f"  - Satellite Alt/Az: {alt_sat.dstr()}, {az_sat.dstr()}")
           print(f"  - Angular separation: {difference_angle}\n")
    
    
#add function to graph position of target and any satellites that cross -  3d with ra, dec, time/2d antimated over time? 

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
    
    global earth
    global warkworth
    global ssb_warkworth
    global ts
    global sats
    
    planets = load('de421.bsp')
    earth = planets['earth']
    
    ts = load.timescale()
    
    sats = selectData("starlink")
    
    warkworth = wgs84.latlon(-36, +174, elevation_m=43)
    ssb_warkworth = earth + warkworth
    
    #example target for observation: barnards star:
    barnard = Star(ra_hours=(17, 57, 48.49803), dec_degrees=(4, 41, 36.2072))
    vela = Star(ra_hours=(8,35,20.65525), dec_degrees=(-45, 10, 35.1545))
    
    #checkOverhead() 
    timeRange(vela, ts.utc(2025,1,1,8,0,0), ts.utc(2025,1,1,8,1,0))

main()

    
