# -*- coding: utf-8 -*-
"""
Window with adjustment controls for tuning master window sizes.

@author: sklykov

@license: MIT license, ref.: https://github.com/sklykov/multip_wins_bpc/blob/main/LICENSE

"""

# %% Global imports
from tkinter import Toplevel, BooleanVar, TOP, LEFT, DoubleVar
from tkinter.ttk import Checkbutton, Style, Spinbox, Frame, Label


# %% Window specification
class AdjustSizesWin(Toplevel):
    """Class wrapper for a window with adjustment of the master window controls."""

    def __init__(self, master_widget, windows_resizable: bool):
        super().__init__(master=master_widget); self.title("Adjust Sizes")
        y_shift = master_widget.master.winfo_y()  # shift of Toplevel window vertically
        x_shift = master_widget.master.winfo_x() + master_widget.master.winfo_width() + 10  # shift of Toplevel window horizontally
        self.geometry(f"+{x_shift}+{y_shift}"); self.pad = 8; self.initial_x_shift = x_shift; self.initial_y_shift = y_shift
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

        # Width and height of the figure from the main window selectors
        self.height_width_frame = Frame(master=self)  # container for both width and height selectors
        # Width selector specification as the Spinbox
        self.width_sel_frame = Frame(master=self.height_width_frame)
        self.width_label = Label(master=self.width_sel_frame, text="Figure width: ")
        self.width_value = DoubleVar(); self.width_value.set(self.master.figure_size_w)
        self.width_selector = Spinbox(master=self.width_sel_frame, from_=2.0, to=12.0, increment=0.2, width=4,
                                      textvariable=self.width_value, command=self.width_changed_by_arrow)
        self.width_label.pack(side=LEFT, padx=self.pad//2, pady=self.pad//2)
        self.width_selector.pack(side=LEFT, padx=self.pad//2, pady=self.pad//2)
        self.width_sel_frame.pack(side=LEFT, padx=self.pad//2, pady=self.pad//2)
        # Height selector specification as the Spinbox
        self.height_sel_frame = Frame(master=self.height_width_frame)
        self.height_label = Label(master=self.height_sel_frame, text="Figure height: ")
        self.height_value = DoubleVar(); self.height_value.set(self.master.figure_size_h)
        self.height_selector = Spinbox(master=self.height_sel_frame, from_=2.0, to=12.0, increment=0.2, width=4, textvariable=self.height_value)
        self.height_label.pack(side=LEFT, padx=self.pad//2, pady=self.pad//2)
        self.height_selector.pack(side=LEFT, padx=self.pad//2, pady=self.pad//2)
        self.height_sel_frame.pack(side=LEFT, padx=self.pad//2, pady=self.pad//2)

        # Placing buttons on the Toplevel window in the single column
        self.resize_switch_btn.pack(side=TOP, padx=self.pad, pady=self.pad)
        self.height_width_frame.pack(side=TOP, padx=self.pad, pady=self.pad)

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

    def width_changed_by_arrow(self):
        """
        Width value changed by arrows.

        Returns
        -------
        None.

        """
        self.master.figure_size_w = self.width_value.get()
        self.master.reinitialize_image_figure()  # Reinitialize the figure with updated sizes
        x_shift = self.master.master.winfo_x() + self.master.master.winfo_width() + 10  # shift of Toplevel window horizontally
        self.geometry(f"+{x_shift}+{self.initial_y_shift}")  # shift this window next to the master one
