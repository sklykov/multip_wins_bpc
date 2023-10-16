# -*- coding: utf-8 -*-
"""
Main GUI script.

@author: sklykov

@license: MIT license, ref.: https://github.com/sklykov/multip_wins_bpc/blob/main/LICENSE

"""

# %% Global imports
import tkinter as tk
import platform
import ctypes
from pathlib import Path

# %% Local imports
if __name__ == "__main__" or __name__ == Path(__file__).stem or __name__ == "__mp_main__":
    from containers.adjust_sizes_ctrls_win import AdjustSizesWin
else:
    from .containers.adjust_sizes_ctrls_win import AdjustSizesWin

# %% Script-wide parameters
__start_message__ = "Main controlling GUI boiler-plate class, MIT licensed, 2023"


# %% GUI based on tkinter.Frame
class MainCtrlUI(tk.Frame):
    """GUI based on tkinter.Frame composing all main controls."""

    def __init__(self, master):
        super().__init__(master)  # initialize the Frame - container for all controls below
        self._relaunch = False  # flag for relaunching again this frame with changed showing parameters
        self.focus_set()  # switch focus to the Frame, working if launched from Python console
        self.master.title("Main Controlling"); self.screen_width = self.master.winfo_screenwidth()
        self.screen_height = self.master.winfo_screenheight()
        # Below - put the main window on the (+x, +y) coordinate away from the top left of the screen
        self.master.geometry(f"+{self.screen_width//4}+{self.screen_height//5}")
        # self.master.resizable(False, False)  # prevent resizing of the master window
        # Variables default values
        self.adjust_sizes_win = None

        # Adding menu bar to the master window (root window)
        self.menubar = tk.Menu(self.master); self.master.config(menu=self.menubar)
        self.actions_menu = tk.Menu(master=self.menubar, tearoff=0)  # tearoff options removes link for opening a Menu in an additional window
        self.actions_menu.add_command(label="Adjust Sizes", command=self.adjust_sizes)
        self.menubar.add_cascade(label="Actions", menu=self.actions_menu)

    def adjust_sizes(self):
        """
        Open additional window for adjusting sizes of this main window.

        Returns
        -------
        None.

        """
        if self.adjust_sizes_win is None:
            self.adjust_sizes_win = AdjustSizesWin(master_widget=self)
        else:
            if self.adjust_sizes_win.winfo_exists():
                self.adjust_sizes_win.destroy(); self.adjust_sizes_win = None
            else:
                del self.adjust_sizes_win; self.adjust_sizes_win = None
                self.adjust_sizes_win = AdjustSizesWin(master_widget=self)


# %% Wrapper UI class
class WrapperMainUI():
    """Wrapper for main GUI Frame."""

    def __init__(self):
        print(__start_message__)
        WrapperMainUI.fix_blurring()  # fix blurring of UIs
        self.tk_root = tk.Tk()  # main tkinter class

    def launch(self):
        """
        Launch main loop of tkinter.Frame and relaunch it if the showing settings changed.

        Returns
        -------
        None.

        """
        self.mainUI = MainCtrlUI(self.tk_root); self.mainUI.mainloop()
        if self.mainUI._relaunch:  # relaunch the main GUI window, if some showing settings changed
            del self.mainUI; self.mainUI = None; self.launch()

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
