# -*- coding: utf-8 -*-
"""Export from 'cameras' module."""

if __name__ != "__main__" and __name__ != "__mp_main__":
    from .simulated import SimulatedCamera

__description__ = "Automatic Import Resolving"

__all__ = ['SimulatedCamera', '__description__']
