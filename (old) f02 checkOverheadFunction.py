#NOTE - CODE NO LONGER USED

import csv
from skyfield.api import EarthSatellite, load

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
    
    main()
