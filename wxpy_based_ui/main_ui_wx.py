# -*- coding: utf-8 -*-
"""
Experimenting with wxpython and wxmplot libraries for replicating features of an app based on tkinter.

@author: sklykov

@license: MIT license, ref.: https://github.com/sklykov/multip_wins_bpc/blob/main/LICENSE

"""
# %% Dev comments
# Some keywords, tricks, bypassing are suggested by AI chat. It speeds up development but makes to avoid reading the whole documentation.
# Even simple task to show noisy uint8 image is difficult on wxmplot (ver. 2025.1.3)

# %% Global imports
import numpy as np
import wx  # main GUI library, wrapper around C++ library
import wxmplot  # additional library providing wrapper around matplotlib to add its plots into the wx widget
import matplotlib.cm as cmap
import matplotlib.pyplot as plt
import time


# %% Custom implementation of UI classes
class MainWxApp(wx.App):
    """Customized wx App class."""

    def __init__(self, title: str = "Custom wx App", win_size: tuple = (480, 420)):
        super().__init__()  # use initialize logic of a parent
        self.main_frame = MainFrame(title=title, size=win_size)  # Frame as the main container for all other widgets
        self.main_frame.Show()  # launches the Frame container
        self.MainLoop()  # launches Event Loop apparently


class MainFrame(wx.Frame):
    """Customized wx Frame class - main widgets (container) for other widgets."""

    def __init__(self, parent=None, title: str = "Main Frame", size: tuple = (420, 380)):
        super().__init__(parent, title=title, size=size)
        self.Centre()  # centering the app window on the center of a screen

        # Creating action button
        self.widget_panel = wx.Panel(parent=self); self.widget_panel.SetBackgroundColour("dark blue")
        self.action_btn = wx.Button(parent=self.widget_panel, label="Action")
        self.action_btn2 = wx.Button(parent=self.widget_panel, label="Another Action")

        # Creating image container
        img_size = (300, 300)
        self.img_container = wxmplot.ImagePanel(parent=self.widget_panel, messenger=messanger_overwrite)
        self.current_img = np.random.randint(0, high=255, size=img_size, dtype=np.uint8)  # dummy image - just noise
        # Note: flag isn't easily retrievable from source code / documentation, and it doesn't work properly for uint8
        # self.img_container.display(self.current_img, auto_contrast=True)
        # self.img_container.display(self.current_img, clim=(0, 255))  # doesn't work as well, wrong contrast
        # self.img_container.display(self.current_img.copy().astype(np.float64), auto_contrast=True)  # doesn't work as well, wrong contrast
        # self.img_container.display(self.current_img.copy().astype(float), auto_contrast=True)  # doesn't work properly
        self.converted_img = self.current_img.copy().astype(np.float64)  # explicit conversion for referring to it below
        # self.img_container.display(self.converted_img, clim=(np.min(self.converted_img), np.max(self.converted_img)))  # doesn't help
        self.converted_img /= np.max(self.converted_img)  # normalizing to the max value
        self.img_container.display(self.converted_img, auto_contrast=True)  # this solution finally works for making a good contrast
        # self.img_container.axes.set_position([0, 0, 1, 1])  # removes all paddings in a plot
        self.img_container.axes.set_aspect('auto')  # fits image to a container
        self.img_container.conf.cmap = cmap.gray; self.img_container.redraw()

        # Layout for placing widgets
        self.main_grid = wx.GridBagSizer(vgap=4, hgap=4)  # flexible grid, no borders from edge of Frame made
        self.main_grid.Add(self.action_btn, pos=(0, 0)); self.main_grid.Add(self.action_btn2, pos=(0, 1))
        self.main_grid.Add(self.img_container, pos=(1, 0), span=(6, 4), flag=wx.EXPAND)

        # Set growable rows and columns
        self.main_grid.AddGrowableCol(0); self.main_grid.AddGrowableRow(1)  # growable cols/rows allows to placed their widget to grow
        self.widget_panel.SetSizerAndFit(self.main_grid)  # suggested as a method to call sizer action
        self.SetMinSize(self.GetBestSize())  # restrict minimal size of a Frame to minimal sizes of widgets inside it

        # Bring focus explicitly to the main window + bring it to the front. Disabled button or other widget automatically getting a focus
        self.Raise(); self.SetFocus()


def messanger_overwrite(*args, **kwargs):
    """
    Empty function for replacing standard messanger for preventing in stdout cursor moving.

    Parameters
    ----------
    *args : list with arguments
        List as a generic container.
    **kwargs : list with key arguments
        List as a generic container.

    Returns
    -------
    None.

    """
    pass


# %% Test as the main script
if __name__ == "__main__":
    # Confirm that noisy uint8 image can be easily shown on matplotlib figure
    confirm_noisy_img = False  # flag for plotting below
    if confirm_noisy_img:
        plt.close('all')
        if not plt.isinteractive():
            plt.ion()
        noisy_image = np.random.randint(0, high=255, size=(300, 300), dtype=np.uint8)
        plt.figure("Simple noisy uint8 image"); plt.imshow(noisy_image, cmap=cmap.gray)
        plt.axis('off'); plt.tight_layout()

    # Launch wx GUI
    wxapp = MainWxApp(); time.sleep(0.1)
    del wxapp  # explicit cleaning of variable, after several launches
