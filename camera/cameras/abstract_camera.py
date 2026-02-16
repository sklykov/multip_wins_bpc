# -*- coding: utf-8 -*-
"""
Camera abstract class that should be inherited by the actual camera controlling class.

@author: sklykov, @license: MIT license

"""
# %% Global imports
from abc import ABC, abstractmethod


# %% Class def.
class AbstractCamera(ABC):
    """Abstract class with methods what should be implemented by the camera controlling classes."""

    @abstractmethod
    def __init__(self):
        """Add placeholder for possible imports."""
        pass

    @abstractmethod
    def initialize(self) -> bool:
        """
        Open (initialize) connection to a camera.

        Returns
        -------
        None.

        """
        pass

    @abstractmethod
    def initialization_status(self) -> str:
        """
        Provide problem report after calling initialize() method.

        Returns
        -------
        str
            Camera initialization status.

        """
        pass

    @abstractmethod
    def close(self):
        """
        Close the connection.

        Returns
        -------
        None.

        """
        pass

    @abstractmethod
    def snap_image(self):
        """
        Snap single image.

        Returns
        -------
        None.

        """
        pass

    @property  # this decorator turns the method into readable-only class attribute
    @abstractmethod
    def camera_type() -> str:
        """
        Camera type should be specified.

        Returns
        -------
        str
            Camera type for exporting the the calling method.

        """
        pass

    def is_valid_class_name(self) -> bool:
        """
        Check actual camera class name for validity and further auto import in the main module.

        Returns
        -------
        bool
            True, if actual camera class has "Camera" in it, like class "SimulatedCamera".

        """
        class_name = self.__class__.__name__  # getting the actual runtime class name for an instance (child class)
        return "Camera" in class_name  # returns True if the camera class name is valid (contains "Camera" in it)

    @abstractmethod
    def access_camera_settings(self):
        """
        Open external window with controllable camera settings (available for a OpenCV wrapper for an embedded camera).

        Returns
        -------
        None.

        """
        pass

    @abstractmethod
    def lock_unlock_settings(self, lock_state: bool):
        """
        Abstract method for locking / unlocking explicitly if any settings can be set.

        Parameters
        ----------
        lock_state : bool
            If True, all settings will be ignored and not set.

        Returns
        -------
        None.

        """
        pass

    @property
    @abstractmethod
    def camera_settings(cls) -> dict:
        """
        Should be implemented by each camera for providing a dict for set camera parameters available.

        Returns
        -------
        dict
            Stored camera settings which could be accessed and set.

        """
        pass
