# -*- coding: utf-8 -*-
"""
Embedded camera class controlled by OpenCV methods.

@author: sklykov, @license: MIT license

"""
# %% Global imports
import numpy as np
from pathlib import Path
import platform
import warnings
from typing import Union

# Basic check that pyopencv library installed
global pyopencv_installed
pyopencv_installed = False
try:
    import cv2; global cv2
    if cv2 is not None:
        pyopencv_installed = True
except ModuleNotFoundError:
    pass

# %% Local imports
if __name__ == "__main__" or __name__ == Path(__file__).stem or __name__ == "__mp_main__":
    from abstract_camera import AbstractCamera
else:
    from .abstract_camera import AbstractCamera

# %% Auto exports
__all__ = ['EmbeddedLaptopCamera']


# %% Class def.
class EmbeddedLaptopCamera(AbstractCamera):
    """Embedded in Laptop camera control."""

    available_camera_settings : dict = {}  # placeholder for a compatibility, all settings controlled through external window

    def __init__(self):
        self.camera_index = 0  # default camera index
        self.camera_handle = None; self.lock_camera_settings = False
        self.exp_t_ms = 0; self.img_width = 0; self.img_height = 0
        self.camera_report = ""  # default - empty report (no problems)
        self.platform = str(platform.system()).lower()
        if "windows" in self.platform:
            self.backend = cv2.CAP_DSHOW
        elif "linux" in self.platform:
            self.backend = cv2.CAP_V4L2
        elif "darwin" in self.platform:
            self.backend = cv2.CAP_AVFOUNDATION
        else:
            __mess = "\nNot recognized OS (platform): " + self.platform + "\n Checked ones: windows, linux, darwin"
            self.backend = 0; warnings.warn(__mess)  # 0 - recommended as default parameter

    def camera_type() -> str:
        """
        Return displayed on UI camera name used as a camera type.

        Returns
        -------
        str
            Camera name for UI (type).

        """
        return "Laptop_Emb"

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
        Open camera logic.

        Returns
        -------
        None.

        """
        if pyopencv_installed:
            # Search for a camera from indices 0, 1, ... 5
            for i in range(0, 6, 1):
                camera = cv2.VideoCapture(i, self.backend)
                if camera.isOpened():
                    print(f"Camera with index {i} is opened on OS '{self.platform}' with used backend: {camera.getBackendName()}", flush=True)
                    self.camera_handle = camera; self.img_width = camera.get(cv2.CAP_PROP_FRAME_WIDTH)
                    self.img_height = camera.get(cv2.CAP_PROP_FRAME_HEIGHT); break
            if self.camera_handle is not None and self.camera_handle.isOpened():
                self.camera_report = ""; return True
            else:
                self.camera_report = "No available camera has been found, check avaibility of an embedded camera"; return False
        else:
            self.camera_report = "Required library 'pyopencv' not installed"; return False

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
        numpy.ndarray
            2D matrix as the image.

        """
        read_flag, frame = self.camera_handle.read()  # read single frame
        if read_flag:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # required conversion from BGR to RGB, because default is BGR
            return frame
        else:
            return None

    def access_camera_settings(self):
        """
        Open external window with all available settings.

        Returns
        -------
        None.

        """
        if not self.lock_camera_settings:
            self.camera_handle.set(cv2.CAP_PROP_SETTINGS, 1)  # open external window with all available settings

    def set_and_report_prop(self, prop: int, value: float) -> Union[float, None]:
        """
        Set some property value and get the result afterwards for checking if it is ignored.

        Parameters
        ----------
        prop : int
            cv2.propId of the property.
        value : float
            Some value to set.

        Returns
        -------
        float or None
            Actual value if set.

        """
        if self.camera_handle is not None and self.camera_handle.isOpened():
            self.camera_handle.set(prop, value)
            return self.camera_handle.get(prop)
        return None

    def lock_unlock_settings(self, lock_state: bool):
        """
        Lock and unlock possibility to open an external window with settings.

        Parameters
        ----------
        lock_state : bool
            If True, no settings window will be opened.

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
        if self.camera_handle is not None and self.camera_handle.isOpened():
            self.camera_handle.release(); cv2.destroyAllWindows()
