# -*- coding: utf-8 -*-
"""
Simulated (for images generation only containing noise) camera class.

@author: sklykov, @license: MIT license

"""
# %% Global imports
import time
import numpy as np
from pathlib import Path
import random


# %% Local imports
if __name__ == "__main__" or __name__ == Path(__file__).stem or __name__ == "__mp_main__":
    from abstract_camera import AbstractCamera
else:
    from .abstract_camera import AbstractCamera

# %% Auto exports
__all__ = ['SimulatedCamera']


# %% Class def.
class SimulatedCamera(AbstractCamera):
    """Simulated camera with the noise simulation."""

    available_camera_settings : dict = {"Exposure Time": {"min": 1, "max": 2000, "type": int, "current": 50, "unit": "ms", "step": 1},
                                        "Max Acq. Random Delay": {"min": 0, "max": 11, "type": int, "current": 3, "unit": "ms", "step": 1}}

    def __init__(self):
        self.exposure_time = self.available_camera_settings["Exposure Time"]["current"]
        self.acq_random_delay = self.available_camera_settings["Max Acq. Random Delay"]["current"]
        self.lock_camera_settings = False  # flag for locking possibility to set anything
        print("Simulated Camera class initialized", flush=True); time.sleep(self.exposure_time/1000)

    def camera_type() -> str:
        """
        Return "Simulated".

        Returns
        -------
        str
            Camera name.

        """
        return "Simulated"

    def camera_settings(cls) -> dict:
        """
        Return controllable camera parameters.

        Returns
        -------
        dict
            Dictionary with available camera settings controls along with min / max range.

        """
        return cls.available_camera_settings

    def initialize(self) -> bool:
        """
        Open camera logic.

        Returns
        -------
        None.

        """
        time.sleep(0.005); return True

    def initialization_status(self) -> str:
        """
        Return constant string "Initialized".

        Returns
        -------
        str
            "Initialized".

        """
        return "Initialized"

    def snap_image(self) -> np.ndarray:
        """
        Generate random (noisy) picture.

        Returns
        -------
        numpy.ndarray
            2D matrix as the image.

        """
        exp_time_offset = random.randint(0, self.acq_random_delay)  # random selection of integer delay for acquisition
        time.sleep((self.exposure_time + exp_time_offset)/1000)  # wait for an exposure time + some overhead
        return np.random.randint(0, high=255, size=(480, 640), dtype='uint8')

    def access_camera_settings(self):
        """
        Wrap a method, controlling lift off for the window managed from the main window.

        Returns
        -------
        None.

        """
        pass

    def lock_unlock_settings(self, lock_state: bool):
        """
        Set lock / unlock state explicitly.

        Parameters
        ----------
        lock_state : bool
            Automatic.

        Returns
        -------
        None.

        """
        self.lock_camera_settings = lock_state

    def close(self):
        """
        Close camera logic.

        Returns
        -------
        None.

        """
        time.sleep(0.008)
