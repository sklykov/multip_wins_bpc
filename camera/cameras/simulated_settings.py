# -*- coding: utf-8 -*-
"""
Simulated (for images generation only containing noise) camera settings window.

@author: sklykov, @license: MIT license

"""
# %% Global imports
from tkinter import LEFT, IntVar, TOP, Frame, BOTH
from tkinter.ttk import Label, Spinbox

try:
    import tkthread; tkthread.patch()  # fix the errors reported after closing the GUI: "RuntimeError: main thread is not in main loop"
except ModuleNotFoundError:
    print("Please install 'tkthread' from https://pypi.org/project/tkthread/ for making tkinter thread-safe", flush=True)


# %% GUI class
class SimulatedSettings(Frame):
    """Widget with controlling of Simulated camera properties."""

    def __init__(self, master, ctrl_class):

        super().__init__(master)  # initialize the Frame - container for all controls below
        self.padx = 4; self.pady = 4
        self.focus_set()  # switch focus to the Frame, working if launched from Python console
        self.master.title("Simulated Cam. Settings")

        # Exposure time control as Spinbox
        self.exp_time_sel_frame = Frame(master=self)
        self.exp_time_label = Label(master=self.exp_time_sel_frame, text="Exposure Time [ms]: ")
        self.exp_time_value = IntVar(); self.exp_time_value.set(ctrl_class.exposure_time)
        self.exp_time_selector = Spinbox(master=self.exp_time_sel_frame, from_=ctrl_class.camera_settings["Exposure Time"]["min"],
                                         to=ctrl_class.camera_settings["Exposure Time"]["max"],
                                         increment=1, width=5, textvariable=self.exp_time_value, command=self.set_exp_time)
        self.exp_time_label.pack(side=LEFT, padx=self.padx//2, pady=self.pady//2)
        self.exp_time_selector.pack(side=LEFT, padx=self.padx//2, pady=self.pady//2)
        self.exp_time_selector.bind('<Return>', self.set_exp_time); self.exp_time_selector.bind('<FocusOut>', self.set_exp_time)

        # Placing elements
        self.exp_time_sel_frame.pack(side=TOP, padx=self.padx, pady=self.pady)
        self.pack(fill=BOTH); self.update()  # commands for finally show all packed widgets

    def set_exp_time(self, *args):
        pass
