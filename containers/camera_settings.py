# -*- coding: utf-8 -*-
"""
Simulated (for images generation only containing noise) camera settings window.

@author: sklykov, @license: MIT license

"""
# %% Global imports
from tkinter import LEFT, IntVar, TOP, Frame, DoubleVar, Toplevel
from tkinter.ttk import Label, Spinbox
from pathlib import Path
import numpy as np

try:
    import tkthread; tkthread.patch()  # fix the errors reported after closing the GUI: "RuntimeError: main thread is not in main loop"
except ModuleNotFoundError:
    print("Please install 'tkthread' from https://pypi.org/project/tkthread/ for making tkinter thread-safe", flush=True)

# %% Local imports
if __name__ == "__main__" or __name__ == Path(__file__).stem or __name__ == "__mp_main__":
    from spinbox_wrapper import SpinboxWrapper
else:
    from .spinbox_wrapper import SpinboxWrapper


# %% GUI class
class CamSettings(Toplevel):
    """Widget with controlling of Simulated camera properties."""

    def __init__(self, master):
        super().__init__(master); self.padx = 4; self.pady = 4; self.focus_set() # working if launched from Python console
        self.focus_force(); self.title("Camera Settings"); self.ctrl_btns = []
        # shift this window relative to the master one first vertically, after - horizontally
        y_shift = master.master.winfo_y(); x_shift = master.master.winfo_x() + master.master.winfo_width() + 10
        self.geometry(f"+{x_shift}+{y_shift}")

        # Exposure time control as Spinbox
        if "Exposure Time" in self.master.camera_settings.keys():
            self.exp_time_sel_frame = Frame(master=self); unit_label = self.master.camera_settings["Exposure Time"]["unit"]
            self.exp_time_label = Label(master=self.exp_time_sel_frame, text=f"Exposure Time [{unit_label}]: ")
            self.min_exp_time = self.master.camera_settings["Exposure Time"]["min"]
            self.max_exp_time = self.master.camera_settings["Exposure Time"]["max"]
            increment_step = self.master.camera_settings["Exposure Time"]["step"]; max_n_digits = len(str(abs(self.max_exp_time)))
            if self.master.camera_settings["Exposure Time"]["type"] == "int":
                self.exp_time_value = IntVar()
            elif self.master.camera_settings["Exposure Time"]["type"] == "float":
                self.exp_time_value = DoubleVar()
            self.exp_time_value.set(self.master.camera_settings["Exposure Time"]["current"])
            self.exp_time_selector = Spinbox(master=self.exp_time_sel_frame, from_=self.min_exp_time, to=self.max_exp_time,
                                             increment=increment_step, width=max_n_digits+1, textvariable=self.exp_time_value,
                                             command=self.set_exp_time)
            self.exp_time_wrapper = SpinboxWrapper(spinbox_button=self.exp_time_selector, associated_value=self.exp_time_value,
                                                   min_value=self.min_exp_time, max_value=self.max_exp_time)
            self.exp_time_label.pack(side=LEFT, padx=self.padx, pady=self.pady)
            self.exp_time_selector.pack(side=LEFT, padx=self.padx, pady=self.pady)
            self.exp_time_selector.bind('<Return>', self.set_exp_time); self.exp_time_selector.bind('<FocusOut>', self.set_exp_time)
            self.exp_time_sel_frame.pack(side=TOP, padx=self.padx, pady=self.pady)  # place on a UI widget
            self.ctrl_btns.append(self.exp_time_selector)  # place in the list of implemented buttons

        self.lock_unlock_buttons()  # !!! Whenver new button added, add lock / unlock to this method

        # Placing elements
        self.update()  # commands for finally show all packed widgets

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
        if self.exp_time_wrapper.validate_input():
            self.master.lock_ui_btns(); self.lock_unlock_buttons()
            if self.master.camera_settings["Exposure Time"]["type"] == "int":
                self.master.send_cmd2camera(("Set Exposure Time", int(self.exp_time_value.get())))
            elif self.master.camera_settings["Exposure Time"]["type"] == "float":
                self.master.send_cmd2camera(("Set Exposure Time", float(self.exp_time_value.get())))
            trigger_set = self.master.trigger_camera_data.wait(timeout=0.5)
            if trigger_set:
                self.master.trigger_camera_data.clear(); self.master.retrieve_updated_settings()
            else:
                print("Something wrong with the Set Exposure Time logic, the TIMEOUT happened in a trigger wait function", flush=True)
            self.master.fps_snaps_stream = 0; self.master.ring_fps_buffer = np.zeros((5, )); self.master.index_fps_buffer = 0
            self.master.acquired_images = 0; self.master.fps = 0
            self.master.unlock_ui_btns(); self.lock_unlock_buttons()
        self.focus_set()

    def update_shown_values(self):
        """
        Update values according to the stored settings on the main window.

        Returns
        -------
        None.

        """
        if "Exposure Time" in self.master.camera_settings.keys():
            self.exp_time_value.set(self.master.camera_settings["Exposure Time"]["current"])

    def lock_unlock_buttons(self):
        """
        Lock and unlock buttons depending on a camera state.

        Returns
        -------
        None.

        """
        for btn in self.ctrl_btns:
            if self.master.block_btns_flag:
                btn.config(state="disabled")
            else:
                btn.config(state="normal")
