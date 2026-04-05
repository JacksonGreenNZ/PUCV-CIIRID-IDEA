import csv
from pathlib import Path
from datetime import datetime
from core.run_config import RunConfig
from models.beam_model import BeamModel
from core.observer import Observer
from core.checker import InterferenceChecker
from core.sopp_runner import SOPPRunner
from visualisation.sky_plot import SkyPlot
from core.window_analyser import WindowAnalyser
from config import TIME_BEGIN, TIME_END, GAP_TOLERANCE_SECONDS
from config import (
    LATITUDE, LONGITUDE, ELEVATION_M,
    DISH_DIAMETER_M, FREQUENCY_HZ,
    RA_HOURS, DEC_DEGREES,
    TIME_BEGIN, TIME_END,
    GAP_TOLERANCE_SECONDS, GAIN_CUTOFF_PERCENT,
    DATA_TYPE
)

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(), #print to terminal       
        logging.FileHandler("outputs/rfi.log"), #save to file
    ]
)

log = logging.getLogger(__name__)

def save_animation(beam_model, observer, results, output_dir, timestamp):
    log.warning("Saving video. Warning - may take some time.")
    plot_filename = output_dir / f"sky_plot_{timestamp}.mp4"
    plot = SkyPlot(beam_model, observer, results)
    plot.animate(save_path=str(plot_filename))

def main(run_config: RunConfig = None):
    if run_config is None:
        #CLI constructs from config.py
        run_config = RunConfig(
            latitude=LATITUDE,
            longitude=LONGITUDE,
            elevation_m=ELEVATION_M,
            dish_diameter_m=DISH_DIAMETER_M,
            frequency_hz=FREQUENCY_HZ,
            ra_hours=RA_HOURS,
            dec_degrees=DEC_DEGREES,
            time_begin=TIME_BEGIN,
            time_end=TIME_END,
            gap_tolerance_seconds=GAP_TOLERANCE_SECONDS,
            gain_cutoff_percent=GAIN_CUTOFF_PERCENT,
            data_type=DATA_TYPE,
        )
        
    #initialise core components
    tle_file = SOPPRunner.select_data(run_config.data_type)
    beam_model = BeamModel()
    observer = Observer()
    
    log.debug(f"Prefilter radius: {beam_model.prefilter_radius_deg:.4f} degrees")

    #run SOPP
    runner = SOPPRunner(beam_model, run_config, tle_file)
    interference_events = runner.run()
    log.info(f"SOPP returned {len(interference_events)} events")

    #run Airy check
    checker = InterferenceChecker(beam_model, observer)
    results = checker.check(interference_events)
    log.info(f"Airy check flagged {len(results)} position points")

    analyser = WindowAnalyser(results, run_config.time_begin, run_config.time_end)
    log.info(analyser.clean_stretches_summary(gap_tolerance_seconds=run_config.gap_tolerance_seconds))
    #write CSV
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    csv_filename = output_dir / f"sat_intersect_{timestamp}.csv"

    fieldnames = [
        "time_utc", "satellite", "sat_alt_deg", "sat_az_deg",
        "target_alt_deg", "target_az_deg", "angular_sep_deg", "gain_percent"
    ]

    with open(csv_filename, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    log.info(f"Wrote {len(results)} entries to {csv_filename}")    
    log.info("Analysis Complete.")
    return beam_model, observer, results, output_dir, timestamp

if __name__ == "__main__":
    beam_model, observer, results, output_dir, timestamp = main()
    animate = input("Would you like to save the animation? (y/n): ").strip().lower() == 'y'
    if animate:     
        save_animation(beam_model, observer, results, output_dir, timestamp)