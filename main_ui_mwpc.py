# -*- coding: utf-8 -*-
"""
Main GUI script - visualization of images stream.

@author: sklykov

@license: MIT license, ref.: https://github.com/sklykov/multip_wins_bpc/blob/main/LICENSE

"""

# %% Global imports
from tkinter import Frame, Menu, Tk, font
from tkinter.ttk import Button, Style
import platform
import ctypes
from pathlib import Path
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # import canvas container from matplotlib for tkinter
import matplotlib.figure as pltFigure   # matplotlib figure for showing images
import time

# %% Local imports
if __name__ == "__main__" or __name__ == Path(__file__).stem or __name__ == "__mp_main__":
    from containers.adjust_sizes_ctrls_win import AdjustSizesWin
else:
    from .containers.adjust_sizes_ctrls_win import AdjustSizesWin

# %% Script-wide parameters
__start_message__ = "Main controlling GUI boiler-plate class, MIT licensed, 2023"


# %% GUI based on tkinter.Frame
class MainCtrlUI(Frame):
    """GUI based on tkinter.Frame composing all main controls."""

    def __init__(self, master, changed_dpp: bool = False):
        super().__init__(master)  # initialize the Frame - container for all controls below
        self._relaunch = False  # flag for relaunching again this frame with changed showing parameters
        self.focus_set()  # switch focus to the Frame, working if launched from Python console
        self.master.title("Main Controlling Window"); self.screen_width = self.master.winfo_screenwidth()
        self.screen_height = self.master.winfo_screenheight()
        # Below - put the main window on the (+x, +y) coordinate away from the top left of the screen
        self.master.geometry(f"+{self.screen_width//4}+{self.screen_height//5}")
        self._changed_dpi = changed_dpp  # for disabling width / height controlling of an image

        # Default values of GUI provided by tkinter (for adjusting on the separate window)
        self.main_font = font.nametofont("TkDefaultFont"); self.entry_font = font.nametofont("TkTextFont"); self.menu_font = font.nametofont("TkMenuFont")
        if self.main_font.cget("size") <= 9:
            self.main_font.config(size=self.main_font.cget("size") + 1)  # increase by 1 default font size
        if self.entry_font.cget("size") <= 9:
            self.entry_font.config(size=self.entry_font.cget("size") + 1)  # increase by 1 default font size

        # Default values of variables used in the methods
        self.adjust_sizes_win = None; self.windows_resizable = True
        self.figure_size_w = 5.6; self.figure_size_h = 5.2  # default width and height, measured in inches

        # Adding menu bar to the master window (root window)
        self.menubar = Menu(self.master); self.master.config(menu=self.menubar)
        # tearoff options removes link for opening a Menu in an additional window
        self.actions_menu = Menu(master=self.menubar, tearoff=0, font=self.menu_font)
        self.actions_menu.add_command(label="Adjust Sizes", command=self.adjust_sizes)
        self.menubar.add_cascade(label="Actions", menu=self.actions_menu)

        # Figure for showing of images
        self.image_figure = pltFigure.Figure(figsize=(self.figure_size_w, self.figure_size_h))  # empty figure with default sizes (WxH)
        self.image_canvas = FigureCanvasTkAgg(self.image_figure, master=self); self.plot_widget = self.image_canvas.get_tk_widget()

        # Buttons
        self.single_click_btn_style = Style(); self.single_click_btn_style_name = 'Custom1.TButton'
        self.single_click_btn_style.configure(self.single_click_btn_style_name, foreground='blue')  # Make specific styling of ttk.Button
        self.snap_image_btn = Button(master=self, text="Snap Image", command=self.snap_image, style=self.single_click_btn_style_name)

        # Put widgets, buttons on the Frame (window) on the grid layout
        self.padx = 6; self.pady = 6
        self.plot_widget.grid(row=0, rowspan=18, column=0, columnspan=10, padx=self.padx, pady=self.pady)
        self.snap_image_btn.grid(row=0, rowspan=1, column=10, columnspan=1, padx=self.padx, pady=self.pady)
        self.grid(); self.master.update()  # for showing all placed widgets in the grid layout

    # %% Functionality
    def snap_image(self):
        """
        Acquire single image from the camera.

        Returns
        -------
        None.

        """
        pass

    # %% Adjusting GUI
    def adjust_sizes(self):
        """
        Open additional window for adjusting sizes of this main window.

        Returns
        -------
        None.

        """
        if self.adjust_sizes_win is None:
            self.adjust_sizes_win = AdjustSizesWin(master_widget=self, windows_resizable=self.windows_resizable)
        else:
            if self.adjust_sizes_win.winfo_exists():
                self.adjust_sizes_win.destroy(); self.adjust_sizes_win = None
            else:
                self.adjust_sizes_win = None; self.adjust_sizes_win = AdjustSizesWin(master_widget=self, windows_resizable=self.windows_resizable)

    def reinitialize_image_figure(self):
        """
        Reinitialize the figure with update sizes.

        Returns
        -------
        None.

        """
        self.plot_widget.destroy(); self.image_canvas = None; self.image_figure = None   # delete widget and variables by deleting references
        self.image_figure = pltFigure.Figure(figsize=(self.figure_size_w, self.figure_size_h))  # empty figure with default sizes (WxH)
        self.image_canvas = FigureCanvasTkAgg(self.image_figure, master=self); self.plot_widget = self.image_canvas.get_tk_widget()
        self.plot_widget.grid(row=0, rowspan=18, column=0, columnspan=10, padx=self.padx, pady=self.pady); self.master.update()

    def relaunch_gui(self):
        """
        Register destroying of GUI window and this class for further relaunching of both.

        It is needed for applying changed tkinter settings (like font size).

        Returns
        -------
        None.

        """
        self._relaunch = True
        if self.adjust_sizes_win is not None:
            if self.adjust_sizes_win.winfo_exists():
                self.adjust_sizes_win.destroy(); self.adjust_sizes_win = None
        self.after(25, self.master.destroy)


# %% Wrapper UI class
class WrapperMainUI():
    """Wrapper for main GUI Frame."""

    def __init__(self):
        print(__start_message__)
        WrapperMainUI.fix_blurring()  # fix blurring of UIs
        self.tk_root = Tk()  # main tkinter class, toplevel window

    def launch(self):
        """
        Launch main loop of tkinter.Frame and relaunch it if the showing settings changed.

        Returns
        -------
        None.

        """
        self.mainUI = MainCtrlUI(self.tk_root); self.mainUI.mainloop()
        while self.mainUI._relaunch:  # relaunch the main GUI window, if some showing settings changed
            dpi_changed = self.mainUI._changed_dpi
            time.sleep(0.01); self.tk_root = Tk()  # reinitialize main GUI class
            self.mainUI = MainCtrlUI(self.tk_root, dpi_changed); self.mainUI.mainloop()  # initialize again GUI based on Frame()

    @staticmethod
    def fix_blurring():
        """
        Fix the issue with blurring if the script is launched on Windows.

        Returns
        -------
        None.

        """
        if platform.system() == "Windows":
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
            except (FileNotFoundError, ModuleNotFoundError):
                pass


# %% Testing
if __name__ == "__main__":
    ctrl_cls = WrapperMainUI(); ctrl_cls.launch()
