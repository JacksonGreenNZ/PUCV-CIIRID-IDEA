import numpy as np
from scipy.special import j1
from scipy.optimize import brentq
from config import DISH_DIAMETER_M, FREQUENCY_HZ, GAIN_CUTOFF_PERCENT

class BeamModel:
    def __init__(self):
        self.diameter = DISH_DIAMETER_M
        self.wavelength = 3e8 / FREQUENCY_HZ
        self.threshold = GAIN_CUTOFF_PERCENT / 100.0
        self.prefilter_radius_deg = self._compute_prefilter_radius()

    def _airy_gain(self, theta_deg):
        '''
        provide angular distance from target, recieve gain at that point based on airy radiation pattern
        
        :param theta_deg: angular separation (deg)
        '''
        
        theta_rad = np.radians(theta_deg)
        x = np.pi * self.diameter * np.sin(theta_rad) / self.wavelength
        if np.isclose(x, 0):
            return 1.0
        return (2 * j1(x) / x) ** 2

    def _compute_prefilter_radius(self): 
        '''
        scan from 90 degrees inward to find outermost angle above threshold; use to find the radius to pass to SOPP interference checker
        '''
        angles = np.linspace(89.9, 0.01, 50000)
        for i, theta in enumerate(angles):
            if self._airy_gain(theta) >= self.threshold:
                return brentq(
                    lambda t: self._airy_gain(t) - self.threshold,
                    angles[i], angles[i - 1]
                )
        return 0.0

    def gain_at_angle(self, theta_deg):
        '''
        provide angular distance from target, recieve gain at that point based on airy radiation pattern
        
        :param theta_deg: angular separation (deg)
        '''
        return self._airy_gain(theta_deg)

    def is_interfering(self, theta_deg):
        '''
        Compares beam strength where the satellite is to the threshold established
        
        :param theta_deg: Description
        '''
        return self.gain_at_angle(theta_deg) >= self.threshold