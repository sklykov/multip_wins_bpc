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
class CamSettings(Frame):
    """Widget with controlling of Simulated camera properties."""

    def __init__(self, master):

        # TODO: implement
        super().__init__(master)  # initialize the Frame - container for all controls below
        self.padx = 4; self.pady = 4
        self.focus_set()  # switch focus to the Frame, working if launched from Python console
        self.master.title("Camera Settings")

        # Exposure time control as Spinbox
        self.exp_time_sel_frame = Frame(master=self)
        self.exp_time_label = Label(master=self.exp_time_sel_frame, text="Exposure Time [ms]: ")
        self.exp_time_value = IntVar(); self.exp_time_value.set(self.camera_ctrl_cls.exposure_time)
        self.min_exp_time = self.camera_ctrl_cls.camera_settings["Exposure Time"]["min"]
        self.max_exp_time = self.camera_ctrl_cls.camera_settings["Exposure Time"]["max"]
        self.exp_time_selector = Spinbox(master=self.exp_time_sel_frame, from_=self.min_exp_time, to=self.max_exp_time,
                                         increment=1, width=5, textvariable=self.exp_time_value, command=self.set_exp_time)
        self.exp_time_label.pack(side=LEFT, padx=self.padx//2, pady=self.pady//2)
        self.exp_time_selector.pack(side=LEFT, padx=self.padx//2, pady=self.pady//2)
        self.exp_time_selector.bind('<Return>', self.set_exp_time); self.exp_time_selector.bind('<FocusOut>', self.set_exp_time)

        self.lock_unlock_buttons()  # !!! Whenver new button added, add lock / unlock to this method

        # Placing elements
        self.exp_time_sel_frame.pack(side=TOP, padx=self.padx, pady=self.pady)
        self.pack(fill=BOTH); self.update()  # commands for finally show all packed widgets

    def set_exp_time(self, *args):
        """
        Set exposure time on the camera class.

        Parameters
        ----------
        *args : list
            Provided by tkinter.

        Returns
        -------
        None.

        """
        try:
            exp_time = int(self.exp_time_value.get())
            if self.min_exp_time <= exp_time <= self.max_exp_time:
                self.camera_ctrl_cls.exposure_time = exp_time
            else:
                self.exp_time_value.set(self.camera_ctrl_cls.exposure_time)
        except ValueError:
            self.exp_time_value.set(self.camera_ctrl_cls.exposure_time)

    def lock_unlock_buttons(self):
        """
        Lock and unlock buttons depending on a camera state.

        Returns
        -------
        None.

        """
        if self.camera_ctrl_cls.lock_camera_settings:
            self.exp_time_selector.config(state="disabled")
        else:
            self.exp_time_selector.config(state="normal")
