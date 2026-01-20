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
from tkinter import Tk
import platform
import ctypes


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
        self.exposure_time = 50; self.camera_settings = {"Exposure Time": {"min": 1, "max": 2000}}
        print("Simulated Camera class initialized", flush=True); time.sleep(self.exposure_time/1000)
        if platform.system() == "Windows":
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except (FileNotFoundError, ModuleNotFoundError):
                pass
        self.root_tk = Tk(); self.camera_settings_win = None

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
        exp_time_offset = random.randint(0, 3)  # random selection of integer offset
        time.sleep((self.exposure_time + exp_time_offset)/1000)  # wait for an exposure time + some overhead
        return np.random.randint(0, high=255, size=(480, 640), dtype='uint8')

    def access_camera_settings(self):
        """
        Open external window with available camera controls.

        Returns
        -------
        None.

        """
        if self.camera_settings_win is None:
            pass
        else:
            pass

    def close(self):
        """
        Close camera logic.

        Returns
        -------
        None.

        """
        if self.root_tk is not None:
            self.root_tk.destroy()
        time.sleep(0.008)
