import numpy as np
from scipy.special import j1
from scipy.optimize import brentq

class BeamModel:
    def __init__(self, dish_diameter_m: float, frequency_hz: float, gain_cutoff_percent: float = 3.0, bypass: bool = False):
        self.diameter = dish_diameter_m
        self.wavelength = 3e8 / frequency_hz if frequency_hz != 0 else 0
        self.threshold = gain_cutoff_percent / 100.0
        self.bypass = bypass
        self.prefilter_radius_deg = 0.0 if bypass else self.compute_prefilter_radius()

    def airy_gain(self, theta_deg):
        '''
        provide angular distance from target, recieve gain at that point based on airy radiation pattern
        
        :param theta_deg: angular separation (deg)
        '''
        if self.wavelength == 0:
            return 50 #extra handling just in case on bypass
        theta_rad = np.radians(theta_deg)
        x = np.pi * self.diameter * np.sin(theta_rad) / self.wavelength
        if np.isclose(x, 0):
            return 1.0
        return (2 * j1(x) / x) ** 2

    def compute_prefilter_radius(self): 
        '''
        scan from 90 degrees inward to find outermost angle above threshold; use to find the radius to pass to SOPP interference checker
        '''
        angles = np.linspace(89.9, 0.01, 50000)
        for i, theta in enumerate(angles):
            if self.airy_gain(theta) >= self.threshold:
                return brentq(
                    lambda t: self.airy_gain(t) - self.threshold,
                    angles[i], angles[i - 1]
                )
        return 0.0

    def interference_gain(self, theta_deg):
        """
        returns gain percent if above threshold, none if below
    
        :param theta_deg: angular separation in degrees
        """
        gain = self.airy_gain(theta_deg)
        if self.bypass:
            return gain * 100
        if gain >= self.threshold:
            return gain * 100
        return None