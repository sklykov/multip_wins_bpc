# -*- coding: utf-8 -*-
"""
Window with adjustment controls for tuning master window sizes.

@author: sklykov

@license: MIT license, ref.: https://github.com/sklykov/multip_wins_bpc/blob/main/LICENSE

"""

# %% Global imports
from tkinter import Toplevel


# %% Window specification
class AdjustSizesWin(Toplevel):
    """Class wrapper for a window with adjustment of the master window controls."""

    def __init__(self, master_widget):
        super().__init__(master_widget)
        self.title("Adjust Sizes")
        # self.protocol("WM_DELETE_WINDOW", self.close)  # Window close rewritting
