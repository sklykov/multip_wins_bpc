# -*- coding: utf-8 -*-
"""
Basler area camera basic control.

@author: sklykov, @license: MIT license

"""
# %% Global imports
import numpy as np
from pathlib import Path
from typing import Union
import time
import traceback

# Basic check that pyopencv library installed
global pypylon_installed
pypylon_installed = False
try:
    import pypylon; global pypylon
    if pypylon is not None:
        pypylon_installed = True
except ModuleNotFoundError:
    pass

# %% Local imports
if __name__ == "__main__" or __name__ == Path(__file__).stem or __name__ == "__mp_main__":
    from abstract_camera import AbstractCamera
else:
    from .abstract_camera import AbstractCamera

# %% Auto exports
__all__ = ['BaslerAreaCamera']


# %% Class def.
class BaslerAreaCamera(AbstractCamera):
    """Basler area camera basic control."""

    available_camera_settings : dict = {"Exposure Time": {"min": 0.01, "max": 500.0, "type": "float", "current": 50.0,
                                                          "unit": "ms", "step": 0.01}}

    def __init__(self):
        self.camera_handle = None; self.camera_report = ""  # default - empty report (no problems)
        self.exp_t_ms = self.available_camera_settings["Exposure Time"]["current"]; self.img_width = 0; self.img_height = 0
        self.standard_delay_ms = 3; self.standard_delay_s = self.standard_delay_ms*1E-3; self.standard_timeout_snap_ms = 1000

    def camera_type() -> str:
        """
        Return displayed on UI camera name used as a camera type.

        Returns
        -------
        str
            Camera name for UI (type).

        """
        return "Basler_Area"

    def camera_settings(cls) -> dict:
        """
        Return controllable camera parameters.

        Returns
        -------
        dict
            Available for control camera settings.

        """
        return cls.available_camera_settings

    def initialize(self) -> bool:
        """
        Initialize connection to the camera.

        Returns
        -------
        None.

        """
        if pypylon_installed:
            try:
                from pypylon import pylon
                tl_factory = pylon.TlFactory.GetInstance(); devices = None; devices = tl_factory.EnumerateDevices()  # Discover devices
                if devices is not None and len(devices) > 0:
                    self.camera_handle = pylon.InstantCamera(tl_factory.CreateFirstDevice())
                    time.sleep(self.standard_delay_s); self.camera_handle.Open(); time.sleep(self.standard_delay_s)
                    if self.camera_handle is not None and self.camera_handle.IsOpen():
                        self.camera_handle.Width.SetValue(self.camera_handle.Width.Max); self.img_width = self.camera_handle.Width.Max
                        self.camera_handle.Height.SetValue(self.camera_handle.Height.Max); self.img_height = self.camera_handle.Height.Max
                        self.camera_handle.PixelFormat.SetValue("Mono12")  # default for the monocolor camera types (can be changed)
                        self.camera_handle.ExposureAuto.SetValue("Off")  # switch off auto exposure (setting automatically exposure time)
                        self.camera_handle.ExposureTime.SetValue(1E3*self.exp_t_ms)  # set fixed exposure time - default
                        self.camera_report = ""; return True
                    else:
                        self.camera_report = "Basler camera not opened (maybe is already connected)"; return False
                else:
                    self.camera_report = "No available Basler camera has been found, check connection to a camera"; return False
            except ImportError:
                self.camera_report = f"Most likely problem in 'pypolon' library import:\n{traceback.format_exc()}"; return False
            except Exception:
                self.camera_report = f"Thrown Exception during Basler camera Initialization:\n{traceback.format_exc()}"; return False
        else:
            self.camera_report = "Required library 'pypylon' not installed"; return False

    def initialization_status(self) -> str:
        """
        Return stored problem report during initialization.

        Returns
        -------
        str
            Stored problem report.

        """
        return self.camera_report

    def snap_image(self) -> Union[np.ndarray, None]:
        """
        Generate random (noisy) picture.

        Returns
        -------
        numpy.ndarray or None
            2D matrix as the image.

        """
        current_image = None  # default value
        with self.camera_handle.GrabOne(self.standard_timeout_snap_ms) as res:
            current_image = res.Array.copy()
        return current_image

    def set_exposure_time(self, exp_time_ms: float):
        """
        Set exposure time of a camera.

        Parameters
        ----------
        exp_time_ms : float
            Provided by a wrapper and in turn by a control window.

        Returns
        -------
        None.

        """
        self.lock_camera_settings = True  # flag for possible reusage for locking other requests (if any)
        if not isinstance(exp_time_ms, float):
            exp_time_ms = round(float(exp_time_ms), 2)
        self.camera_handle.ExposureTime.SetValue(1E3*exp_time_ms); self.exp_t_ms = self.camera_handle.ExposureTime.GetValue()
        self.available_camera_settings["Exposure Time"]["current"] = self.exp_t_ms
        print("Set on Basler Camera Exp.Time [ms]:", self.exp_t_ms, flush=True)
        self.lock_camera_settings = False

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

    def access_camera_settings(self):
        """
        Implement abstract method.

        Returns
        -------
        None.

        """
        pass

    def close(self):
        """
        Close camera logic.

        Returns
        -------
        None.

        """
        if self.camera_handle is not None and self.camera_handle.IsOpen():
            self.camera_handle.Close(); time.sleep(self.standard_delay_s)
