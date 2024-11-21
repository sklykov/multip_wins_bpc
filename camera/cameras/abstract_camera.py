# -*- coding: utf-8 -*-
"""
Camera abstract class.

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
    def initialize():
        """
        Open (initialize) connection to a camera.

        Returns
        -------
        None.

        """
        pass

    @abstractmethod
    def close():
        """
        Close the connection.

        Returns
        -------
        None.

        """
        pass

    @abstractmethod
    def snap_image():
        """
        Snap single image.

        Returns
        -------
        None.

        """
        pass

    @property
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
