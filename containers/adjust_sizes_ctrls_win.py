# -*- coding: utf-8 -*-
"""
Window with adjustment controls for tuning master window sizes.

@author: sklykov

@license: MIT license, ref.: https://github.com/sklykov/multip_wins_bpc/blob/main/LICENSE

"""

# %% Global imports
from tkinter import Toplevel, BooleanVar, TOP
from tkinter.ttk import Checkbutton, Style


# %% Window specification
class AdjustSizesWin(Toplevel):
    """Class wrapper for a window with adjustment of the master window controls."""

    def __init__(self, master_widget, windows_resizable: bool):
        super().__init__(master=master_widget); self.title("Adjust Sizes")
        y_shift = master_widget.master.winfo_y()  # shift of Toplevel window vertically
        x_shift = master_widget.master.winfo_x() + master_widget.master.winfo_width() + 10  # shift of Toplevel window horizontally
        self.geometry(f"200x140+{x_shift}+{y_shift}"); self.pad = 8
        # self.protocol("WM_DELETE_WINDOW", self.close)  # Window close rewritting

        # Custom styling for on / off states
        self.checkbtn_style = Style(); self.checkbtn_style_name = 'Custom1.TCheckbutton'  # name of Layout should exist!

        # Buttons and commands specification
        self.resize_state = BooleanVar(); self.resize_state.set(windows_resizable)
        self.text_resize_btn_dis = "Disable Resizing"; self.text_resize_btn_en = "Enable Resizing"
        self.master.master.resizable(self.resize_state.get(), self.resize_state.get())
        if windows_resizable:
            text_btn = self.text_resize_btn_dis; fg_color = 'blue'
        else:
            text_btn = self.text_resize_btn_en; fg_color = 'green'
        self.checkbtn_style.configure(self.checkbtn_style_name, foreground=fg_color)
        self.resize_switch_btn = Checkbutton(master=self, text=text_btn, command=self.resize_switch, onvalue=True,
                                             offvalue=False, variable=self.resize_state, style=self.checkbtn_style_name)

        # Placing buttons on the Toplevel window in the single column
        self.resize_switch_btn.pack(side=TOP, padx=self.pad, pady=self.pad)

    # %% Methods
    def resize_switch(self):
        """
        Enable / disable resizing of opened windows.

        Returns
        -------
        None.

        """
        if self.resize_state.get():
            self.resize_switch_btn.config(text=self.text_resize_btn_dis)
            self.checkbtn_style.configure(self.checkbtn_style_name, foreground='blue')
        else:
            self.resize_switch_btn.config(text=self.text_resize_btn_en)
            self.checkbtn_style.configure(self.checkbtn_style_name, foreground='green')
        self.master.master.resizable(self.resize_state.get(), self.resize_state.get())  # regulate resizing of the master window
        self.resizable(self.resize_state.get(), self.resize_state.get()); self.master.windows_resizable = self.resize_state.get()
