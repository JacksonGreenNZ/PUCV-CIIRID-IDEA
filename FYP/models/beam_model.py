import numpy as np
from typing import cast
from scipy.special import j1
from scipy.optimize import brentq

class BeamModel:
    """
    Models the antenna radiation pattern using an Airy disk approximation.

    The Airy pattern describes the far-field diffraction gain of a circular
    aperture (dish) as a function of angular offset from boresight. It is used
    both to pre-filter satellite candidates via a beamwidth radius passed to
    SOPP, and to evaluate per-event gain for interference classification.

    :param dish_diameter_m: Physical dish diameter in metres.
    :param frequency_hz: Observation frequency in Hz. Used to derive wavelength.
    :param gain_cutoff_percent: Minimum gain (as % of peak) to flag as
        interfering. Defaults to 3%.
    :param bypass: If True, skip the Airy pattern and treat the beam as a
        top-hat defined by manual_beamwidth_deg. gain is returned as 100%
        for all separations within that beamwidth.
    """

    def __init__(self, dish_diameter_m: float, frequency_hz: float, gain_cutoff_percent: float = 3.0, bypass: bool = False):
        self.diameter = dish_diameter_m
        self.wavelength = 3e8 / frequency_hz if frequency_hz != 0 else 0
        self.threshold = gain_cutoff_percent / 100.0
        self.bypass = bypass
        self.prefilter_radius_deg = 0.0 if bypass else self.compute_prefilter_radius()

    def airy_gain(self, theta_deg: float) -> float:
        """
        Compute the normalised Airy disk gain at a given angular offset.

        Uses the formula G(θ) = [2 J₁(x) / x]², where x = π·D·sin(θ)/λ,
        D is dish diameter and λ is wavelength. Returns 1.0 at boresight
        (θ = 0) and falls off with increasing angular separation.

        :param theta_deg: Angular separation from boresight in degrees.
        :returns: Normalised gain in [0, 1], where 1.0 is peak (boresight).
        """
        if self.wavelength == 0:
            return 50 #extra handling just in case on bypass
        theta_rad = np.radians(theta_deg)
        x = np.pi * self.diameter * np.sin(theta_rad) / self.wavelength
        if np.isclose(x, 0):
            return 1.0
        return (2 * j1(x) / x) ** 2

    def compute_prefilter_radius(self) -> float:
        """
        Find the outermost angular radius at which gain exceeds the threshold.

        Scans from 90° inward and uses Brent's method to refine the crossing
        point. The result is passed to SOPP as the beamwidth, so only
        satellites within this cone are evaluated by the interference checker.

        :returns: Prefilter radius in degrees, or 0.0 if no crossing is found.
        """
        angles = np.linspace(89.9, 0.01, 50000)
        for i, theta in enumerate(angles):
            if self.airy_gain(theta) >= self.threshold:
                return cast(float, brentq(
                    lambda t: self.airy_gain(t) - self.threshold,
                    angles[i], angles[i - 1]
                ))
        return 0.0

    def interference_gain(self, theta_deg: float) -> float | None:
        """
        Return the gain percentage at the given offset if it exceeds the
        threshold, or None if the satellite is below the interference cutoff.

        In bypass mode, all offsets return a flat 100% gain (top-hat beam).

        :param theta_deg: Angular separation from boresight in degrees.
        :returns: Gain as a percentage of peak (0–100), or None if below threshold.
        """
        if self.bypass:
            return 100.0
        gain = self.airy_gain(theta_deg)
        if gain >= self.threshold:
            return gain * 100
        return None