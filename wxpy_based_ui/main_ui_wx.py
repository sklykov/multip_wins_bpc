# -*- coding: utf-8 -*-
"""
Experimenting with wxpython and wxmplot libraries for replicating features of an app based on tkinter.

@author: sklykov

@license: MIT license, ref.: https://github.com/sklykov/multip_wins_bpc/blob/main/LICENSE

"""
# %% Dev comments

# %% Global imports
import numpy as np
import wx
import wxmplot


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
        self.btn_panel = wx.Panel(parent=self); self.btn_panel.SetBackgroundColour("dark blue")
        self.action_btn = wx.Button(parent=self.btn_panel, label="Action")
        self.action_btn2 = wx.Button(parent=self.btn_panel, label="Another Action")

        # Creating image container
        img_size = (300, 300)
        self.img_container = wxmplot.ImagePanel(parent=self.btn_panel, size=img_size, messenger=messanger_overwrite)
        self.current_img = np.random.randint(0, high=255, size=img_size, dtype='uint8')
        self.img_container.display(self.current_img)

        # Layout for placing widgets
        self.main_grid = wx.GridBagSizer(vgap=4, hgap=4)  # flexible grid
        self.main_grid.Add(self.action_btn, pos=(0, 0))
        self.main_grid.Add(self.action_btn2, pos=(0, 1))
        self.main_grid.Add(self.img_container, pos=(1, 0), span=(1, 2), flag=wx.EXPAND)
        self.btn_panel.SetSizer(self.main_grid)


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
    wxapp = MainWxApp()
