# -*- coding: utf-8 -*-
"""
Camera abstract class.

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

    def __init__(self):
        self.exp_t_ms = 25
        print("Simulated Camera class initialized", flush=True); time.sleep(self.exp_t_ms/1000)

    def camera_type() -> str:
        """
        Return "Simulated".

        Returns
        -------
        str
            Camera name.

        """
        return "Simulated"

    def initialize(self) -> bool:
        """
        Open camera logic.

        Returns
        -------
        None.

        """
        time.sleep(0.005)
        return True

    def snap_image(self) -> np.ndarray:
        """
        Generate random (noisy) picture.

        Returns
        -------
        numpy.ndarray
            2D matrix as the image.

        """
        exp_time_offset = random.randint(0, 3)  # random selection of integer offset
        time.sleep((self.exp_t_ms + exp_time_offset)/1000)  # wait for an exposure time + some overhead
        return np.random.randint(0, high=255, size=(480, 640), dtype='uint8')

    def set_exp_time(self, exp_t_ms: int) -> bool:
        """
        Set exposure time in ms.

        Parameters
        ----------
            Exposure time in ms.

        Returns
        -------
        bool
            If check is succesfull and exposure time is set.

        """
        if 0 < exp_t_ms <= 2000:
            self.exp_t_ms = exp_t_ms; return True
        else:
            return False

    def get_exp_time(self) -> int:
        """
        Get stored exposure time in ms.

        Returns
        -------
        int
            Exposure time in ms.

        """
        return self.exp_t_ms

    def close(self):
        """
        Close camera logic.

        Returns
        -------
        None.

        """
        time.sleep(0.008)
