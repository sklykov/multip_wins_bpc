# -*- coding: utf-8 -*-
"""
Camera abstract class.

@author: sklykov, @license: MIT license

"""
# %% Global imports
import time
import numpy as np
from pathlib import Path

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
        print("Simulated Camera class initialized", flush=True); time.sleep(0.025)

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
        time.sleep(21/1000)  # short exposure time
        return np.random.randint(0, high=255, size=(480, 640), dtype='uint8')

    def close(self):
        """
        Close camera logic.

        Returns
        -------
        None.

        """
        time.sleep(0.008)
