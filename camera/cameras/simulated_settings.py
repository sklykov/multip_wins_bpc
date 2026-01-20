# -*- coding: utf-8 -*-
"""
Simulated (for images generation only containing noise) camera settings window.

@author: sklykov, @license: MIT license

"""
# %% Global imports
from tkinter import Frame

try:
    import tkthread; tkthread.patch()  # fix the errors reported after closing the GUI: "RuntimeError: main thread is not in main loop"
except ModuleNotFoundError:
    print("Please install 'tkthread' from https://pypi.org/project/tkthread/ for making tkinter thread-safe")


class SimulatedSettings(Frame):
    pass
