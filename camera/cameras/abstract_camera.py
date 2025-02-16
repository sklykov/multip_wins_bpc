# -*- coding: utf-8 -*-
"""
Camera abstract class that should be inherited by the actual camera controlling class.

@author: sklykov, @license: MIT license

"""
# %% Global imports
from abc import ABC, abstractmethod
from typing import Union


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
    def set_exp_time(self, exp_t_ms: Union[float, int]) -> bool:
        """
        Set exposure time on a camera.

        Parameters
        ----------
        exp_t_ms : Union[float, int]
            Exposure time to set (in any unit).

        Returns
        -------
        bool
            True if provided exposure time has been set.

        """
        pass

    @abstractmethod
    def get_exp_time(self) -> Union[float, int]:
        """
        Get assigned exposure time on a camera.

        Returns
        -------
        Union[float, int]
            Used exposure time.

        """
        pass
