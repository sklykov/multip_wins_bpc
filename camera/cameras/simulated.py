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
        pass

    def camera_type() -> str:
        """
        Return "Simulated".

        Returns
        -------
        str
            Camera name.

        """
        return "Simulated"

    def initialize():
        """
        Open camera logic.

        Returns
        -------
        None.

        """
        time.sleep(0.005)

    def snap_image() -> np.ndarray:
        """
        Generate random (noisy) picture.

        Returns
        -------
        numpy.ndarray
            2D matrix as the image.

        """
        return np.random.randint(0, high=255, size=(480, 640), dtype='uint8')

    def close():
        """
        Close camera logic.

        Returns
        -------
        None.

        """
        time.sleep(0.008)
