# -*- coding: utf-8 -*-
"""
Embedded camera class controlled by OpenCV methods.

@author: sklykov, @license: MIT license

"""
# %% Global imports
import numpy as np
from pathlib import Path

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

    def __init__(self):
        self.camera_index = 0  # default camera index
        self.camera_handle = None; self.exp_t_changeable = False
        self.exp_t_ms = 0; self.img_width = 0; self.img_height = 0
        self.camera_report = ""  # default - empty report (no problems)

    def camera_type() -> str:
        """
        Return "Laptop_Embedded".

        Returns
        -------
        str
            Camera name.

        """
        return "Laptop_Embedded"

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
                camera = cv2.VideoCapture(i)
                if camera.isOpened():
                    print(f"Camera with index {i} is available and will be used", flush=True)
                    current_exposure_value = camera.get(cv2.CAP_PROP_EXPOSURE)
                    if current_exposure_value > 0.0:
                        self.exp_t_changeable = True; self.exp_t_ms = current_exposure_value
                    self.img_width = camera.get(cv2.CAP_PROP_FRAME_WIDTH); self.img_height = camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
                    self.camera_handle = camera; break
            if self.camera_handle is not None and self.camera_handle.isOpened():
                self.camera_report = ""
                return True
            else:
                self.camera_report = "No available camera has been found, check avaibility of an embedded camera"
                return False
        else:
            self.camera_report = "Required library 'pyopencv' not installed"
            return False

    def initialization_status(self) -> str:
        """
        Return stored problem report during initialization.

        Returns
        -------
        str
            Stored problem report.

        """
        return self.camera_report

    def snap_image(self) -> np.ndarray:
        """
        Generate random (noisy) picture.

        Returns
        -------
        numpy.ndarray
            2D matrix as the image.

        """
        read_flag, frame = self.camera_handle.read()  # read single frame
        if read_flag:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # required conversion from BGR to RGB
            return frame
        else:
            return None

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
            if self.exp_t_changeable:
                try:
                    self.camera_handle.set(cv2.CAP_PROP_EXPOSURE, exp_t_ms)  # trying to set exposure time
                    self.exp_t_ms = self.camera_handle.get(cv2.CAP_PROP_EXPOSURE)  # getting an exposure time acknowledged by a camera
                except Exception:
                    return False
                return True
            else:
                return False
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
        if self.camera_handle is not None and self.camera_handle.isOpened():
            self.camera_handle.release(); cv2.destroyAllWindows()
