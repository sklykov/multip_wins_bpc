# -*- coding: utf-8 -*-
"""
Main GUI script - visualization of images stream.

@author: sklykov

@license: MIT license, ref.: https://github.com/sklykov/multip_wins_bpc/blob/main/LICENSE

"""

# %% Dev comments
# Overall note: tkinter isn't good for complex GUI development, planning to switch to another GUI library
# The issue: if the main window has not been closed before using adjusting the window sizes, cannot be relaunched in the IPython console.
# It needs to be relaunched

# %% Global imports
try:
    import tkthread; tkthread.patch()  # fix the errors reported after closing the GUI: "RuntimeError: main thread is not in main loop"
except ModuleNotFoundError:
    print("Please install 'tkthread' from https://pypi.org/project/tkthread/ for making tkinter thread-safe")
# Ref. to the package above: https://pypi.org/project/tkthread/  Note that the license is Apache Software License.
from tkinter import Frame, Menu, Tk, font, LEFT, TOP, BOTH, StringVar
from tkinter.ttk import Button, Style, Label, OptionMenu
from tkinter.ttk import Frame as ttkFrame
import platform
import ctypes
from pathlib import Path
import matplotlib.pyplot as plt; plt.ion()
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # import canvas container from matplotlib for tkinter
import matplotlib.figure as pltFigure   # matplotlib figure for showing images
import time
import inspect
from datetime import datetime  # for getting current year
from multiprocessing import Queue, Event
from queue import Empty

# %% Local imports
if __name__ == "__main__" or __name__ == Path(__file__).stem or __name__ == "__mp_main__":
    from containers.adjust_sizes_ctrls_win import AdjustSizesWin
    from utils.utility_funcs import clean_mp_queue
    from camera.camera_wrapper import CameraWrapper
else:
    from .containers.adjust_sizes_ctrls_win import AdjustSizesWin
    from .utils.utility_funcs import clean_mp_queue
    from .camera.camera_wrapper import CameraWrapper

# %% Script-wide parameters
current_year = datetime.now().strftime('%Y')
__start_message__ = f"Main Controlling Camera GUI script, {current_year} MIT licensed, GitHub: @sklykov"


# %% GUI based on tkinter.Frame
class MainCtrlUI(Frame):
    """GUI based on tkinter.Frame composing all main controls."""

    def __init__(self, master, changed_dpi: bool = False):
        super().__init__(master)  # initialize the Frame - container for all controls below
        self._relaunch = False  # flag for relaunching again this frame with changed showing parameters
        self.focus_set()  # switch focus to the Frame, working if launched from Python console
        self.master.title("Main Controlling Window"); self.screen_width = self.master.winfo_screenwidth()
        self.screen_height = self.master.winfo_screenheight()
        # Below - put the main window on the (+x, +y) coordinate away from the top left of the screen
        self.master.geometry(f"+{self.screen_width//4}+{self.screen_height//5}")
        self._changed_dpi = changed_dpi  # for disabling width / height controlling of an image
        self.focus_force(); self.padx = 8; self.pady = 8; self.sleep_time_actions_ms = 0.004

        # Default values of GUI provided by tkinter (for adjusting on the separate window)
        self.main_font = font.nametofont("TkDefaultFont"); self.entry_font = font.nametofont("TkTextFont")
        self.menu_font = font.nametofont("TkMenuFont"); self.menu_font_size = self.menu_font.cget("size")
        self.main_font_size = self.main_font.cget("size"); self.entry_font_size = self.entry_font.cget("size")
        if self.main_font_size <= 9:
            self.main_font.config(size=self.main_font.cget("size") + 1)  # increase by 1 default font size
            self.main_font_size += 1
        if self.entry_font_size <= 9:
            self.entry_font.config(size=self.entry_font.cget("size") + 1)  # increase by 1 default font size
            self.entry_font_size += 1

        # Default values of variables used in the methods
        self.adjust_sizes_win = None; self.windows_resizable = True
        self.figure_size_w = 6.2; self.figure_size_h = 5.8  # default width and height, measured in inches

        # Adding menu bar to the master window (root window)
        self.menubar = Menu(self.master); self.master.config(menu=self.menubar)
        # tearoff options removes link for opening a Menu in an additional window
        self.actions_menu = Menu(master=self.menubar, tearoff=0, font=self.menu_font)
        self.actions_menu.add_command(label="Adjust Sizes", command=self.adjust_sizes)
        self.menubar.add_cascade(label="Actions", menu=self.actions_menu)

        # Figure for showing of images
        self.image_figure = pltFigure.Figure(figsize=(self.figure_size_w, self.figure_size_h))  # empty figure with default sizes (WxH)
        self.image_canvas = FigureCanvasTkAgg(self.image_figure, master=self); self.plot_widget = self.image_canvas.get_tk_widget()

        # Select the camera from the list
        self.buttons_frame = Frame(master=self)  # for placing all buttons in it
        self.bg_color = '#52514f'  # some custom dark background color for label and selectable type of the camera
        self.widgets_styles = Style()   # the single class is enough for configuration of different widget names
        self.camera_sel_frame_style_n = 'Custom1.TFrame'; self.widgets_styles.configure(self.camera_sel_frame_style_n, background=self.bg_color)
        self.camera_selector_frame = ttkFrame(master=self.buttons_frame, style=self.camera_sel_frame_style_n)
        self.camera_label_style_name = 'Custom1.TLabel'; self.widgets_styles.configure(self.camera_label_style_name,
                                                                                       foreground='white', background=self.bg_color)
        self.camera_selector_label = Label(master=self.camera_selector_frame, text="Camera: ", style=self.camera_label_style_name)
        self.supported_cameras = ["Simulated", "Physical"]  # list of the names with the supported cameras
        self.selected_camera = StringVar(); self.selected_camera.set(self.supported_cameras[0])
        self.camera_sel_style_name = 'Custom1.TMenubutton'; self.active_camera = self.supported_cameras[0]
        self.widgets_styles.configure(self.camera_sel_style_name, foreground='#FFCD1B', background=self.bg_color)  # dark grey bg, orange fg
        self.camera_selector = OptionMenu(self.camera_selector_frame, self.selected_camera, self.supported_cameras[0], *self.supported_cameras,
                                          style=self.camera_sel_style_name, command=self.change_active_camera)
        self.camera_selector_label.pack(side=LEFT, padx=0, pady=0); self.camera_selector.pack(side=LEFT, padx=0, pady=0)

        # Camera status label - for showing the initialization status of the selected camera
        self.camera_init_status_style = 'Initialized.TLabel'; self.camera_error_status_style = 'Error.TLabel'
        self.widgets_styles.configure(self.camera_init_status_style, foreground='green')
        self.widgets_styles.configure(self.camera_error_status_style, foreground='red')
        self.camera_transition_style = 'Transition.TLabel'; self.widgets_styles.configure(self.camera_transition_style, foreground='orange')
        self.camera_inact_text = "Camera Inactive"; self.camera_act_text = "Camera Active"; self.camera_transit_text = "Waiting..."
        self.camera_status_label = Label(master=self.buttons_frame, text=self.camera_inact_text, style=self.camera_error_status_style)

        # Buttons
        self.single_click_btn_style_name = 'Snap.TButton'; self.widgets_styles.configure(self.single_click_btn_style_name, foreground='blue')
        self.snap_image_btn = Button(master=self.buttons_frame, text="Snap Image", command=self.snap_image,
                                     style=self.single_click_btn_style_name)

        # Placing GUI elements in the container (Frame) which in turn is placed below along with the plot_widget
        self.camera_selector_frame.pack(side=TOP, padx=self.padx, pady=self.pady//2)
        self.camera_status_label.pack(side=TOP, padx=self.padx, pady=self.pady)
        self.snap_image_btn.pack(side=TOP, padx=self.padx, pady=self.pady*2)

        # Pack plot widget with the image and Frame with buttons (grid layout removed)
        self.plot_widget.pack(side=LEFT, padx=self.padx, pady=self.pady)  # The biggest GUI element - image widget
        self.buttons_frame.pack(side=TOP, padx=self.padx, pady=self.pady)  # place container for buttons stick to the top
        self.pack(fill=BOTH); self.update()  # commands for finally show all packed widgets

        # Initialize communication queues and triggers
        self.commands2camera = Queue(maxsize=5); self.data_from_camera = Queue(maxsize=10)
        self.trigger_commands = Event(); self.trigger_camera_data = Event()

        # Initialization of the Simulated camera
        self.camera_process = CameraWrapper(camera_type=self.selected_camera.get(), commands2camera=self.commands2camera,
                                            trigger_commands=self.trigger_commands, data_camera=self.data_from_camera,
                                            trigger_data_camera=self.trigger_camera_data)
        self.camera_process.start(); time.sleep(self.sleep_time_actions_ms)  # starting the CameraWrapper Process loop
        self.camera_status_label.config(text=self.camera_transit_text, style=self.camera_transition_style); self.update()
        trigger_set = False  # for getting the confirmation that the trigger is set
        self.camera_opened = False  # flag for showing that the camera is initialized
        while not self.camera_opened and not trigger_set:
            trigger_set = self.trigger_camera_data.wait(timeout=8.5)  # wait for set trigger with timeout of ... seconds
            if trigger_set:
                self.trigger_camera_data.clear()  # set to the default state
                if not self.data_from_camera.empty():
                    if self.data_from_camera.get_nowait() == "Initialized":
                        print(f"{self.selected_camera.get()} Camera Opened"); self.camera_opened = True
                        self.camera_status_label.config(text=self.camera_act_text, style=self.camera_init_status_style); self.update()
            if not trigger_set or not self.camera_opened:
                print(f"Trigger from {self.selected_camera.get()} Camera not received")
                self.camera_status_label.config(text=self.camera_inact_text, style=self.camera_error_status_style)
                trigger_set = True  # for stopping the loop

    # %% Acquisition
    def snap_image(self):
        """
        Acquire single image from the camera.

        Returns
        -------
        None.

        """
        pass

    # %% Camera control
    def change_active_camera(self, selected_camera):
        """
        Change the active camera.

        Parameters
        ----------
        selected_camera : str
            Provided by tkinter call.

        Returns
        -------
        None.

        """
        if not selected_camera == self.active_camera:  # check that other than the current active camera selected
            print("Selected camera:", selected_camera)
            if not self.check_installed_drivers(selected_camera):
                print(f"The required drivers for the '{selected_camera}' camera not installed. \nThe previously active camera remained")
                self.selected_camera.set(self.active_camera)
            else:
                self.close_camera()  # closing the currently active camera
                self.clean_queues_events()  # cleaning the queues for reconnecting to the new instance of a Camera class
                pass  # initialize the Camera Wrapper class for placing the ctrl logic in the dedicated process

    def check_installed_drivers(self, selected_camera) -> bool:
        """
        Check if the required drivers installed in the current environment.

        Parameters
        ----------
        selected_camera : str
            Provided by the calling method (change_active_camera).

        Returns
        -------
        bool
            Flag if the required drivers not installed in the current environment.

        """
        if selected_camera == "Simulated":
            return True  # default assuming that simulated camera is always available as the fallback
        elif selected_camera == self.supported_cameras[1]:
            return False  # TODO: check 'fluoscenepy' import

    # %% Utilities
    def clean_queues_events(self):
        """
        Clean up queues and set Events to the default state.

        Returns
        -------
        None.

        """
        self.data_from_camera = clean_mp_queue(self.data_from_camera)
        self.commands2camera = clean_mp_queue(self.commands2camera)
        self.trigger_commands.clear(); self.trigger_camera_data.clear()

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
                self.adjust_sizes_win.after(15, self.adjust_sizes_win.destroy); time.sleep(25/1000); self.adjust_sizes_win = None
                # self.adjust_sizes_win.destroy(); self.adjust_sizes_win = None
            else:
                self.adjust_sizes_win = AdjustSizesWin(master_widget=self, windows_resizable=self.windows_resizable)

    def reinitialize_image_figure(self):
        """
        Reinitialize the figure with update sizes.

        Returns
        -------
        None.

        """
        self.plot_widget.destroy(); self.buttons_frame.pack_forget()
        self.image_figure = pltFigure.Figure(figsize=(self.figure_size_w, self.figure_size_h))  # empty figure with changed
        self.image_canvas = FigureCanvasTkAgg(self.image_figure, master=self); self.plot_widget = self.image_canvas.get_tk_widget()
        self.plot_widget.pack(side=LEFT, padx=self.padx, pady=self.pady); self.buttons_frame.pack(side=TOP, padx=self.padx, pady=self.pady)
        self.image_figure.set_figwidth(self.figure_size_w); self.image_figure.set_figheight(self.figure_size_h)

    def adjust_fonts(self):
        """
        Adjust fonts by using changed font sizes on the additional window.

        Returns
        -------
        None.

        """
        self.main_font.config(size=self.main_font_size); self.entry_font.config(size=self.entry_font_size)
        self.menu_font.config(size=self.menu_font_size); self.update()

    def relaunch_gui(self):
        """
        Register relaunch with the special flag for relaunching of the GUI after closing.

        Returns
        -------
        None.

        """
        self._relaunch = True; self.after(40, self.master.destroy)

    # %% Close Main Win. / Camera
    def close_camera(self):
        """
        Quit the CameraWrapper Process loop.

        Returns
        -------
        None.

        """
        if self.camera_opened:
            self.camera_status_label.config(text=self.camera_act_text, style=self.camera_init_status_style); self.update()
            self.commands2camera.put_nowait("Stop"); time.sleep(self.sleep_time_actions_ms); self.trigger_commands.set()
            trigger_set = self.trigger_camera_data.wait(5.5); time.sleep(self.sleep_time_actions_ms)
            if trigger_set:
                try:
                    received_data = self.data_from_camera.get_nowait()
                    if isinstance(received_data, str):
                        print(f"{self.selected_camera.get()} Camera", received_data, "and Closed")
                    else:
                        print("Received from the camera:", received_data)
                    if self.camera_process.is_alive():
                        self.camera_process.join(2.0)
                except Empty:
                    print("Something went wrong with the communication, the CameraWrapper Process will be killed if it's still alive")
                    if self.camera_process.is_alive():
                        self.camera_process.kill()
            else:
                print("Something wrong with the closing logic, the TIMEOUT happened in wait function")
                self.camera_process.kill()
            self.camera_status_label.config(text=self.camera_inact_text, style=self.camera_error_status_style)
            self.camera_opened = False

    def destroy(self):
        """
        Rewrite the behavior of the main window then it's closed.

        Returns
        -------
        None.

        """
        self.close_camera()  # close of a camera logic
        if self.camera_process.is_alive():  # for fallback logic
            print("CameraWrapper Process is still alive, check the closing logic in it."); self.camera_process.join(0.2)
            self.camera_process.kill()
        self.data_from_camera = clean_mp_queue(self.data_from_camera); self.data_from_camera.close()  # cleaning the queue
        self.commands2camera = clean_mp_queue(self.commands2camera); self.commands2camera.close()


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
        self.mainUI = MainCtrlUI(master=self.tk_root); self.mainUI.mainloop()
        while self.mainUI._relaunch:  # relaunch the main GUI window, if some showing settings changed
            dpi_changed = self.mainUI._changed_dpi
            self.tk_root = Tk()  # reinitialize main GUI class
            # initialize again GUI based on Frame()
            self.mainUI = MainCtrlUI(master=self.tk_root, changed_dpi=dpi_changed); self.mainUI.mainloop()

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
    for frame in inspect.stack():
        if "IPython" in str(frame):
            print("NOTE: most probably, this script has been launched in IPython, there it has sometimes the issue with relaunching "
                  + "after using of the adjusting window"); break
    ctrl_cls = WrapperMainUI(); ctrl_cls.launch()
