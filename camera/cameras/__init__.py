# -*- coding: utf-8 -*-
"""Export from 'cameras' module."""

# For automatic discovery of the camera controlling classes, add the imports of camera class below next to SimulatedCamera
# like from .simulated import MyCamera

__description__ = "Automatic Import Resolving"

__all__ = ['__description__']

if __name__ != "__main__" and __name__ != "__mp_main__":
    # ADD below camera controlling classes which should implement methods from the abstract class 'AbstractCamera'
    # See default 'SimulatedCamera' for example of implementation
    from .simulated import SimulatedCamera
    from .laptop_embedded import EmbeddedLaptopCamera
    # Automatuc augmentation of __all__ attribute for auto-exporting classes
    cameras_cls_names = [camera_class for camera_class in locals().keys() if "Camera" in camera_class]
    if len(cameras_cls_names) > 0:
        __all__[1:] = cameras_cls_names[:]
