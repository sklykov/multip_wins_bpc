# -*- coding: utf-8 -*-
"""
Window with adjustment controls for tuning master window sizes.

@author: sklykov

@license: MIT license, ref.: https://github.com/sklykov/multip_wins_bpc/blob/main/LICENSE

"""

# %% Global imports
from tkinter import Toplevel, BooleanVar, TOP, LEFT, DoubleVar, IntVar, Scale
from tkinter.ttk import Checkbutton, Style, Spinbox, Frame, Label, Button
from pathlib import Path
import platform
import time

# %% Local imports
if __name__ == "__main__" or __name__ == Path(__file__).stem or __name__ == "__mp_main__":
    from spinbox_wrapper import SpinboxWrapper
else:
    from .spinbox_wrapper import SpinboxWrapper


# %% Window specification
class AdjustSizesWin(Toplevel):
    """Class wrapper for a window with adjustment of the master window controls."""

    def __init__(self, master_widget, windows_resizable: bool):
        super().__init__(master=master_widget); self.title("Adjust Sizes")
        y_shift = master_widget.master.winfo_y()  # shift of Toplevel window vertically
        x_shift = master_widget.master.winfo_x() + master_widget.master.winfo_width() + 10  # shift of Toplevel window horizontally
        self.geometry(f"+{x_shift}+{y_shift}"); self.pad = 8; self.initial_x_shift = x_shift; self.initial_y_shift = y_shift
        # self.protocol("WM_DELETE_WINDOW", self.close)  # Window close rewritting

        if platform.system() == "Windows":
            # print("Current DPI:", self.master.winfo_pixels('1i'))
            # self.current_scale = round(self.master.winfo_pixels('1i')/72, 1)  # recalculate the scale factor in comparison to 72 DPI
            self.current_dpi = self.master.winfo_pixels('1i')

        # Custom styling for on / off states
        self.checkbtn_style = Style(); self.checkbtn_style_name = 'Custom1.TCheckbutton'  # name of Layout should exist!

        # Buttons and commands specification
        self.resize_state = BooleanVar(); self.resize_state.set(windows_resizable)
        self.text_resize_btn_dis = "Resizing Disabled"; self.text_resize_btn_en = "Resizing Enabled"
        self.master.master.resizable(self.resize_state.get(), self.resize_state.get())
        if windows_resizable:
            text_btn = self.text_resize_btn_en; fg_color = 'green'
        else:
            text_btn = self.text_resize_btn_dis; fg_color = 'red'
        self.checkbtn_style.configure(self.checkbtn_style_name, foreground=fg_color)
        self.resize_switch_btn = Checkbutton(master=self, text=text_btn, command=self.resize_switch, onvalue=True,
                                             offvalue=False, variable=self.resize_state, style=self.checkbtn_style_name)

        # Width and height of the figure from the main window selectors
        self.height_width_frame = Frame(master=self)  # container for both width and height selectors
        self.min_w_h = 2.0; self.max_w_h = 12.0   # min and max selectable width and height of a figure

        # Width selector specification as the Spinbox
        self.width_sel_frame = Frame(master=self.height_width_frame)
        self.width_label = Label(master=self.width_sel_frame, text="Figure width: ")
        self.width_value = DoubleVar(); self.width_value.set(self.master.figure_size_w)
        self.width_selector = Spinbox(master=self.width_sel_frame, from_=self.min_w_h, to=self.max_w_h, increment=0.2, width=4,
                                      textvariable=self.width_value, command=self.width_changed_by_arrow)
        self.width_selector_wr = SpinboxWrapper(self.width_selector, self.width_value, self.min_w_h, self.max_w_h, n_digit_points=1)
        self.width_label.pack(side=LEFT, padx=self.pad//2, pady=self.pad//2); self.width_selector.pack(side=LEFT, padx=self.pad//2, pady=self.pad//2)
        self.width_sel_frame.pack(side=LEFT, padx=self.pad//2, pady=self.pad//2)
        # Height selector specification as the Spinbox
        self.height_sel_frame = Frame(master=self.height_width_frame)
        self.height_label = Label(master=self.height_sel_frame, text="Figure height: ")
        self.height_value = DoubleVar(); self.height_value.set(self.master.figure_size_h)
        self.height_selector = Spinbox(master=self.height_sel_frame, from_=self.min_w_h, to=self.max_w_h, increment=0.2, width=4,
                                       textvariable=self.height_value, command=self.height_changed_by_arrow)
        self.height_selector_wr = SpinboxWrapper(self.height_selector, self.height_value, self.min_w_h, self.max_w_h, n_digit_points=1)
        self.height_label.pack(side=LEFT, padx=self.pad//2, pady=self.pad//2); self.height_selector.pack(side=LEFT, padx=self.pad//2, pady=self.pad//2)
        self.height_sel_frame.pack(side=LEFT, padx=self.pad//2, pady=self.pad//2)

        # Disable width / height adjusting because of the some bug in arrow function call
        if self.master._changed_dpi:
            self.height_selector.config(state="disabled"); self.width_selector.config(state="disabled")

        # Font sizes selectors. Main font (text on labels, buttons) control
        self.font_sizes_frame = Frame(master=self); self.whitespace_label1 = Label(master=self.font_sizes_frame, text=" ")
        self.whitespace_label2 = Label(master=self.font_sizes_frame, text=" ")
        # Default font of texts in buttons and labels
        self.text_font_label = Label(master=self.font_sizes_frame, text="Text Size: ")
        self.text_font_value = IntVar(); self.text_font_value.set(self.master.main_font.cget("size"))
        self.min_text_font = 6; self.max_text_font = 18
        self.text_font_size_sel = Spinbox(master=self.font_sizes_frame, from_=self.min_text_font, to=self.max_text_font,
                                          increment=1, width=3, textvariable=self.text_font_value, command=self.main_font_changed_by_arrow)
        self.text_font_size_sel_wr = SpinboxWrapper(self.text_font_size_sel, self.text_font_value, self.min_text_font, self.max_text_font)
        # Default font of entries (Spinbox values)
        self.entry_font_label = Label(master=self.font_sizes_frame, text="Entry Font: ")
        self.entry_font_value = IntVar(); self.entry_font_value.set(self.master.entry_font.cget("size"))
        self.entry_font_size_sel = Spinbox(master=self.font_sizes_frame, from_=self.min_text_font, to=self.max_text_font,
                                           increment=1, width=3, textvariable=self.entry_font_value, command=self.entry_font_changed_by_arrow)
        self.entry_font_size_sel_wr = SpinboxWrapper(self.entry_font_size_sel, self.entry_font_value, self.min_text_font, self.max_text_font)
        # Menu font control
        self.menu_font_label = Label(master=self.font_sizes_frame, text="Menu Font: ")
        self.menu_font_value = IntVar(); self.menu_font_value.set(self.master.menu_font.cget("size"))
        self.menu_font_size_sel = Spinbox(master=self.font_sizes_frame, from_=self.min_text_font, to=self.max_text_font,
                                          increment=1, width=3, textvariable=self.menu_font_value, command=self.menu_font_changed_by_arrow)
        self.menu_font_size_sel_wr = SpinboxWrapper(self.menu_font_size_sel, self.menu_font_value, self.min_text_font, self.max_text_font)
        # Packing font sizes controllers
        self.text_font_label.pack(side=LEFT, padx=0, pady=self.pad//2); self.text_font_size_sel.pack(side=LEFT, padx=0, pady=self.pad//2)
        self.whitespace_label1.pack(side=LEFT, padx=self.pad//2, pady=self.pad//2)
        self.entry_font_label.pack(side=LEFT, padx=0, pady=self.pad//2); self.entry_font_size_sel.pack(side=LEFT, padx=0, pady=self.pad//2)
        self.whitespace_label2.pack(side=LEFT, padx=self.pad//2, pady=self.pad//2)
        self.menu_font_label.pack(side=LEFT, padx=0, pady=self.pad//2); self.menu_font_size_sel.pack(side=LEFT, padx=0, pady=self.pad//2)

        # Slider for changing the scaling factor
        self.scaling_frame = Frame(master=self); self.scaling_label = Label(master=self.scaling_frame, text="DPI: ")
        self.scaling_slider = Scale(master=self.scaling_frame, resolution=2, from_=int(round(0.75*self.current_dpi, 0)),
                                    to=int(round(1.5*self.current_dpi, 0)), length=200, orient='horizontal', tickinterval=20)
        self.scaling_slider.set(self.current_dpi)
        self.apply_scale_btn = Button(master=self.scaling_frame, command=self.apply_new_scaling, text="Apply DPI",
                                      style=self.master.single_click_btn_style_name)
        self.scaling_label.pack(side=LEFT, padx=0, pady=self.pad//2); self.scaling_slider.pack(side=LEFT, padx=self.pad//2, pady=self.pad//2)
        self.apply_scale_btn.pack(side=LEFT, padx=0, pady=self.pad//2)

        # Associate hit Enter (Return) button with the Spinbox inputs
        # Add all Spinbox (input) buttons and their wrappers into the list for addressing them
        self.inputs = [(self.width_selector, self.width_selector_wr), (self.height_selector, self.height_selector_wr),
                       (self.text_font_size_sel, self.text_font_size_sel_wr), (self.entry_font_size_sel, self.entry_font_size_sel_wr),
                       (self.menu_font_size_sel, self.menu_font_size_sel_wr)]
        for classes_tuple in self.inputs:
            spinbox_button, _ = classes_tuple; spinbox_button.bind('<Return>', self.spinbox_input_enter)  # bind <Return> event for all Spinboxes
            spinbox_button.bind('<FocusOut>', self.spinbox_input_enter)  # bind <FocusOut> event for all Spinboxes

        # Placing buttons on the Toplevel window in the single column
        self.resize_switch_btn.pack(side=TOP, padx=self.pad, pady=self.pad); self.height_width_frame.pack(side=TOP, padx=self.pad, pady=self.pad)
        self.font_sizes_frame.pack(side=TOP, padx=self.pad, pady=self.pad); self.scaling_frame.pack(side=TOP, padx=self.pad, pady=self.pad)

        # self.master.after(2000, self.master.relaunch_gui)  # relaunch after

    # %% Methods
    def resize_switch(self):
        """
        Enable / disable resizing of opened windows.

        Returns
        -------
        None.

        """
        if not self.resize_state.get():
            self.resize_switch_btn.config(text=self.text_resize_btn_dis)
            self.checkbtn_style.configure(self.checkbtn_style_name, foreground='red')
        else:
            self.resize_switch_btn.config(text=self.text_resize_btn_en)
            self.checkbtn_style.configure(self.checkbtn_style_name, foreground='green')
        self.master.master.resizable(self.resize_state.get(), self.resize_state.get())  # regulate resizing of the master window
        self.resizable(self.resize_state.get(), self.resize_state.get()); self.master.windows_resizable = self.resize_state.get()

    def apply_new_scaling(self):
        """
        Apply changed scaling (depends on the selected DPI).

        Returns
        -------
        None.

        """
        if self.current_dpi != self.scaling_slider.get():
            self.master.tk.call('tk', 'scaling', self.scaling_slider.get()/self.current_dpi)
            if not self.master._changed_dpi:
                print("The original scaling will be changed, for returning to the original one, relaunch Python ")
            self.master._changed_dpi = True
            self.master.after(30, self.master.relaunch_gui)  # register the relaunching of the main GUI

    # %% Actions connected with Spinboxes
    def width_changed_by_arrow(self):
        """
        Width of a figure value changed by arrows on UI.

        Returns
        -------
        None.

        """
        self.master.figure_size_w = self.width_value.get()
        # With the combination of tkthread seems that it solves the issue with "main thread is not in main loop" (seems)
        self.master.after(20, self.master.reinitialize_image_figure)
        self.after(35, self.shift_horizontally)

    def height_changed_by_arrow(self):
        """
        Height of a figure value changed by arrows on UI.

        Returns
        -------
        None.

        """
        self.master.figure_size_h = self.height_value.get()
        # With the combination of tkthread seems that it solves the issue with "main thread is not in main loop" (seems)
        self.master.after(20, self.master.reinitialize_image_figure)

    def main_font_changed_by_arrow(self):
        """
        Change the main font by applying value from the Spinbox.

        Returns
        -------
        None.

        """
        self.master.main_font.config(size=self.text_font_value.get()); self.update()
        self.master.update(); self.shift_horizontally(); self.focus_force()

    def entry_font_changed_by_arrow(self):
        """
        Change the size of entry values font by applying value from the Spinbox.

        Returns
        -------
        None.

        """
        self.master.entry_font.config(size=self.entry_font_value.get()); self.update()
        self.master.update(); self.shift_horizontally(); self.focus_force()

    def menu_font_changed_by_arrow(self):
        """
        Change the menu font size by applying value from the Spinbox.

        Returns
        -------
        None.

        """
        self.master.menu_font.config(size=self.menu_font_value.get()); self.update()
        self.master.update(); self.shift_horizontally(); self.focus_force()

    def spinbox_input_enter(self, *args):
        """
        Handle the Enter (Return) button pressing if the Spinbox (input) is active.

        Parameters
        ----------
        *args : str
            Provided by tkinter signature.

        Returns
        -------
        None.

        """
        if len(self.inputs) > 0:
            self.after(12, self.validate_inputs)

    def validate_inputs(self):
        """
        Check all input (Spinbox) buttons for validity of the entered value and make associated method calls.

        Returns
        -------
        None.

        """
        for i, classes_tuple in enumerate(self.inputs):
            _, wrapper_button = classes_tuple
            # Individual assigning of methods for different Spinboxes
            if i == 0:
                if wrapper_button.validate_input():
                    self.after(12, self.width_changed_by_arrow)
            elif i == 1:
                if wrapper_button.validate_input():
                    self.after(12, self.height_changed_by_arrow)
            elif i == 2:
                if wrapper_button.validate_input():
                    self.after(12, self.main_font_changed_by_arrow)
            elif i == 3:
                if wrapper_button.validate_input():
                    self.after(12, self.entry_font_changed_by_arrow)
            elif i == 4:
                if wrapper_button.validate_input():
                    self.after(12, self.menu_font_changed_by_arrow)
            else:
                wrapper_button.validate_input()
        self.focus_set()

    def shift_horizontally(self):
        """
        Shift this window because of some master GUI properties changed.

        Returns
        -------
        None.

        """
        x_shift = self.master.master.winfo_x() + self.master.master.winfo_width() + 10  # shift of Toplevel window horizontally
        self.geometry(f"+{x_shift}+{self.initial_y_shift}")  # shift this window next to the master one
