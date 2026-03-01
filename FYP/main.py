import csv
from pathlib import Path
from datetime import datetime
from models.beam_model import BeamModel
from core.observer import Observer
from core.checker import InterferenceChecker
from core.sopp_runner import SOPPRunner
from visualisation.sky_plot import SkyPlot

def main():
    #initialise core components
    beam_model = BeamModel()
    observer = Observer()
    
    print(f"Prefilter radius: {beam_model.prefilter_radius_deg:.4f} degrees")

    #run SOPP
    runner = SOPPRunner(beam_model)
    interference_events = runner.run()
    print(f"SOPP returned {len(interference_events)} events")

    #run Airy check
    checker = InterferenceChecker(beam_model, observer)
    results = checker.check(interference_events)
    print(f"Airy check flagged {len(results)} position points")

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

    print(f"Wrote {len(results)} entries to {csv_filename}")
    
    #render and save animation
    plot_filename = output_dir / f"sky_plot_{timestamp}.mp4"
    plot = SkyPlot(beam_model, observer, results)
    plot.animate(save_path=str(plot_filename))
    

if __name__ == "__main__":
    main()