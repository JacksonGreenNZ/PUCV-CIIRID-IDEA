from models.beam_model import BeamModel
from core.observer import Observer

class InterferenceChecker:
    """
    Two stage interference pipeline. Uses SOPP pre-filtered events and applies
    Airy gain threshold check to each position point.
    """
    def __init__(self, beam_model: BeamModel, observer: Observer):
        self.beam_model = beam_model
        self.observer = observer

    def check(self, interference_events):
        """
        iterates SOPP interference events, applies Airy gain check to each position point.
        Returns list of dicts for flagged points.

        :param interference_events: list of SOPP interference events
        """
        results = []

        for event in interference_events:
            for pt in event.positions:
                target_alt, target_az = self.observer.get_target_position(pt.time)
                
                ang_sep = self.observer.angular_separation(
                    pt.position.altitude, pt.position.azimuth,
                    target_alt, target_az
                )
                
                gain_percent = self.beam_model.interference_gain(ang_sep)

                if gain_percent is not None:
                    results.append({
                        "time_utc":        pt.time.isoformat(),
                        "satellite":       event.satellite.name,
                        "sat_alt_deg":     pt.position.altitude,
                        "sat_az_deg":      pt.position.azimuth,
                        "target_alt_deg":  target_alt,
                        "target_az_deg":   target_az,
                        "angular_sep_deg": ang_sep,
                        "gain_percent":    gain_percent
                    })

        return results