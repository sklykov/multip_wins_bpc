# -*- coding: utf-8 -*-
"""
Main GUI script - visualization of images stream.

@author: sklykov

@license: MIT license, ref.: https://github.com/sklykov/multip_wins_bpc/blob/main/LICENSE

"""

# %% Dev comments
# Overall note: tkinter isn't good for complex GUI development, planning to switch to another GUI library

# %% Global imports
try:
    import tkthread; tkthread.patch()  # fix the errors reported after closing the GUI: "RuntimeError: main thread is not in main loop"
except ModuleNotFoundError:
    print("Please install 'tkthread' from https://pypi.org/project/tkthread/ for making tkinter thread-safe")
# Ref. to the package above: https://pypi.org/project/tkthread/  Note that the license is Apache Software License.
from tkinter import Frame, Menu, Tk, font, LEFT, TOP, BOTH, StringVar, IntVar
from tkinter.ttk import Button, Style, Label, OptionMenu, Spinbox
from tkinter.ttk import Frame as ttkFrame
import platform
import ctypes
from pathlib import Path
import matplotlib.pyplot as plt; plt.ion()
# import canvas container from matplotlib for tkinter (for toolbar - NavigationToolbar2Tk)
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.figure as pltFigure   # matplotlib figure for showing images
import time
import inspect
from datetime import datetime  # for getting current year
from multiprocessing import Queue, Event
from queue import Empty
import numpy as np

# %% Local imports
if __name__ == "__main__" or __name__ == Path(__file__).stem or __name__ == "__mp_main__":
    from containers.adjust_sizes_ctrls_win import AdjustSizesWin
    from containers.spinbox_wrapper import SpinboxWrapper
    from utils.utility_funcs import clean_mp_queue
    from camera.camera_wrapper import CameraWrapper, cameras_ctrl_types
else:
    from .containers.adjust_sizes_ctrls_win import AdjustSizesWin
    from .utils.utility_funcs import clean_mp_queue
    from .camera.camera_wrapper import CameraWrapper, cameras_ctrl_types
    from .containers.spinbox_wrapper import SpinboxWrapper

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
        self.exp_time_ms = 50  # default value for exposure time - 100 ms, equal to 10 FPS
        self.min_exp_time_ms = 1; self.max_exp_time_ms = 2000  # default range of limits on exposure time
        self.pause_snaps_stream = True  # default flag for preventing too many assigned tasks if pause should be made in a snaps stream

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
        self.adjust_sizes_win = None; self.windows_resizable = False
        self.master.resizable(self.windows_resizable, self.windows_resizable)
        self.figure_size_w = 6.4; self.figure_size_h = 5.9  # default width and height, measured in inches

        # Adding menu bar to the master window (root window)
        self.menubar = Menu(self.master); self.master.config(menu=self.menubar)
        # tearoff options removes link for opening a Menu in an additional window
        self.actions_menu = Menu(master=self.menubar, tearoff=0, font=self.menu_font)
        self.labels_actions_menu = []; self.labels_actions_menu.append("Adjust Sizes")
        for label in self.labels_actions_menu:
            self.actions_menu.add_command(label=label, command=self.adjust_sizes)
        self.menubar.add_cascade(label="Settings", menu=self.actions_menu)

        # Figure for showing of images
        self.image_figure = pltFigure.Figure(figsize=(self.figure_size_w, self.figure_size_h))  # empty figure with default sizes (WxH)
        self.image_canvas = FigureCanvasTkAgg(self.image_figure, master=self); self.plot_widget = self.image_canvas.get_tk_widget()
        self.current_image = None; self.snap_image_obtained = False; self.image_figure_axes = None; self.display_image = False
        self.img_h = None; self.img_w = None
        # Assign subplot to the created figure
        if self.image_figure_axes is None:
            self.image_figure_axes = self.image_figure.add_subplot(); self.image_figure_axes.axis('off'); self.image_figure.tight_layout()
            self.image_figure.subplots_adjust(left=0, bottom=0, right=1, top=1)  # remove white borders
            # self.image_figure_axes.format_coord = self.format_coord
            self.image_figure_axes.format_cursor_data = lambda: ''  # remove pixel value in [...] on a widget
        self.imshowing = None  # AxesImage instance

        # Program parameters, variables
        self.snaps_stream_flag = False; self.snaps_stream_task = None; self.record_flag = False
        self.retain_resizable_flag = False; self.show_image_task = None; self.fast_fps_overhead = 0
        self.fps_snaps_stream = 0

        # Select the camera from the list
        self.buttons_frame = Frame(master=self)  # for placing all buttons in it
        self.bg_color = '#52514f'  # some custom dark background color for label and selectable type of the camera
        self.widgets_styles = Style()   # the single class is enough for configuration of different widget names
        self.camera_sel_frame_style_n = 'Custom1.TFrame'
        self.widgets_styles.configure(self.camera_sel_frame_style_n, background=self.bg_color)
        self.camera_selector_frame = ttkFrame(master=self.buttons_frame, style=self.camera_sel_frame_style_n)
        self.camera_label_style_name = 'Custom1.TLabel'; self.widgets_styles.configure(self.camera_label_style_name,
                                                                                       foreground='white', background=self.bg_color)
        self.camera_selector_label = Label(master=self.camera_selector_frame, text="Camera: ", style=self.camera_label_style_name)
        self.supported_cameras = cameras_ctrl_types  # list of the names with the supported cameras (imported from a module)
        self.supported_cameras.append("Next TBI...")  # add not implemented camera name
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

        self.snap_stream_on_btn_style_name = 'SnapStreamOn.TButton'; self.snap_stream_off_btn_style_name = 'SnapStreamOff.TButton'
        self.snap_stream_on_text = "Start Snaps Stream"; self.snap_stream_off_text = "Stop Snaps Stream"
        self.widgets_styles.configure(self.snap_stream_on_btn_style_name, foreground='#116212', background="#F2F0F2")
        self.widgets_styles.configure(self.snap_stream_off_btn_style_name, foreground='#A61205', background="#F2F0F2")
        self.snap_stream_btn = Button(master=self.buttons_frame, text=self.snap_stream_on_text, command=self.snap_stream,
                                      style=self.snap_stream_on_btn_style_name)

        self.record_stream_on_btn_style_name = 'RecordStreamOn.TButton'; self.record_stream_off_btn_style_name = 'RecordStreamOff.TButton'
        self.record_stream_on_text = "Start Recording"; self.record_stream_off_text = "Stop Recording"
        self.widgets_styles.configure(self.record_stream_on_btn_style_name, foreground='#e32818', background="#dadef5")
        self.widgets_styles.configure(self.record_stream_off_btn_style_name, foreground='#0025d0', background="#f0f1fb")
        self.record_stream_btn = Button(master=self.buttons_frame, text=self.record_stream_on_text, command=self.record_stream,
                                        style=self.record_stream_on_btn_style_name)

        # Exposure time control as Spinbox
        self.exp_time_sel_frame = Frame(master=self.buttons_frame)
        self.exp_time_label = Label(master=self.exp_time_sel_frame, text="Exp. Time (ms): ")
        self.exp_time_value = IntVar(); self.exp_time_value.set(self.exp_time_ms)
        self.exp_time_selector = Spinbox(master=self.exp_time_sel_frame, from_=self.min_exp_time_ms, to=self.max_exp_time_ms,
                                         increment=1, width=5, textvariable=self.exp_time_value, command=self.set_exp_time)
        self.exp_time_selector_wr = SpinboxWrapper(self.exp_time_selector, self.exp_time_value, self.min_exp_time_ms,
                                                   self.max_exp_time_ms, n_digit_points=0)
        self.exp_time_label.pack(side=LEFT, padx=self.padx//2, pady=self.pady//2)
        self.exp_time_selector.pack(side=LEFT, padx=self.padx//2, pady=self.pady//2)
        self.exp_time_selector.bind('<Return>', self.set_exp_time); self.exp_time_selector.bind('<FocusOut>', self.set_exp_time)

        # FPS indicator reported after acquisition
        self.acquired_images = 0; self.fps = 0  # variables
        self.fps_label = Label(master=self.buttons_frame, text=f"Measured FPS: {self.fps}")  # label for showing measured FPS

        # Placing GUI elements in the container (Frame) which in turn is placed below along with the plot_widget
        self.camera_selector_frame.pack(side=TOP, padx=self.padx, pady=self.pady//2)
        self.camera_status_label.pack(side=TOP, padx=self.padx, pady=self.pady)
        self.snap_image_btn.pack(side=TOP, padx=self.padx, pady=self.pady)
        self.snap_stream_btn.pack(side=TOP, padx=self.padx, pady=self.pady)
        self.record_stream_btn.pack(side=TOP, padx=self.padx, pady=self.pady)
        self.exp_time_sel_frame.pack(side=TOP, padx=self.padx, pady=self.pady)
        self.fps_label.pack(side=TOP, padx=self.padx, pady=self.pady)

        # Pack plot widget with the image and Frame with buttons (grid layout removed)
        self.plot_widget.pack(side=LEFT, padx=self.padx, pady=self.pady)  # The biggest GUI element - image widget
        self.buttons_frame.pack(side=TOP, padx=self.padx, pady=self.pady)  # place container for buttons stick to the top
        self.pack(fill=BOTH); self.update()  # commands for finally show all packed widgets

        # Initialize communication queues and triggers
        self.commands2camera = Queue(maxsize=5); self.data_from_camera = Queue(maxsize=10)
        self.trigger_commands = Event(); self.trigger_camera_data = Event()

        # Disabling some buttons at the start
        self.snap_stream_btn.configure(state="disabled"); self.snap_image_btn.configure(state="disabled")
        self.record_stream_btn.configure(state="disabled")

        # Open Simulated camera as a default
        self.open_camera()

    # %% Open camera
    def open_camera(self):
        """
        Wrap camera open logic.

        Returns
        -------
        None.

        """
        # Initialization of the camera (Simulated at the start)
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
                        self.snap_stream_btn.configure(state="normal"); self.snap_image_btn.configure(state="normal")
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
        if self.snaps_stream_flag and not self.record_flag:  # estimation of FPS for snaps stream should be performed in the main UI
            t1 = time.perf_counter()  # will be used for setting FPS setting
        self.commands2camera.put_nowait("Snap"); time.sleep(self.sleep_time_actions_ms/1.5); self.trigger_commands.set()
        trigger_set = self.trigger_camera_data.wait(timeout=5.0); time.sleep(self.sleep_time_actions_ms/1.5)
        # Dev. Note: pausing by time.sleep() makes the snaps stream mode stable
        if trigger_set:
            self.trigger_camera_data.clear()  # set to the default state
            try:
                received_data = self.data_from_camera.get_nowait()
                if isinstance(received_data, np.ndarray):
                    self.current_image = received_data; self.snap_image_obtained = True; self.display_image = True
                    # Check # of acquired images for retrieving measured FPS
                    self.acquired_images += 1   # count number of acquired images
                    if self.acquired_images > 10_000_001:  # auto reset large accumulated # of images
                        self.acquired_images = 1
                    # if not self.record_flag and not self.snaps_stream_flag:
                    #     if self.acquired_images == 3 or self.acquired_images % 50 == 0:  # query measured FPS (3 images or after 50 acquired)
                    #         self.after(9 + self.fast_fps_overhead, self.query_fps)
                    if self.snaps_stream_flag and not self.record_flag:
                        passed_s = round((time.perf_counter() - t1), 9)
                        if self.fps == 0:
                            self.fps = int(round(1.0/passed_s, 0))  # first estimation of FPS
                            self.fps_label.config(text=f"Measured FPS: {self.fps}")  # 1st estimation
                        else:
                            self.fps = int(round(0.5*(self.fps + round(1.0/passed_s, 0)), 0))  # averaging of estimated FPS
                        if self.acquired_images % 5 == 0:  # update FPS each 5 fresh images
                            self.fps_label.config(text=f"Measured FPS: {self.fps}")
                        # Adjust overhead for showing image query
                        if self.fps > 20:
                            self.fast_fps_overhead = 1
                        if self.fps > 50:
                            self.fast_fps_overhead = 2
                        elif self.fps > 75:
                            self.fast_fps_overhead = 3
                        elif self.fps > 100:
                            self.fast_fps_overhead = 4
                    # schedule asynchronous call to show an image with some delays for making GUI more stable
                    self.show_image_task = self.after(7 + self.fast_fps_overhead, self.show_image)
                else:
                    print("Received from the camera:", received_data, flush=True)
                    self.current_image = None; self.display_image = False
            except Empty:
                print("No Image received from Queue, but the trigger is set", flush=True)
                self.current_image = None; self.display_image = False
        else:
            print("Something wrong with the Snap Image logic, the TIMEOUT happened in a trigger wait function", flush=True)
            self.current_image = None; self.display_image = False

    def snap_stream(self):
        """
        Imitates continuous clicking on "Snap Image" button.

        Returns
        -------
        None.

        """
        self.snaps_stream_flag = not self.snaps_stream_flag  # change the flag
        if self.snaps_stream_flag:
            self.snap_image_btn.config(state="disabled")  # disable the single snap button
            self.record_stream_btn.configure(state="normal"); self.exp_time_selector.configure(state="disabled")
            self.retain_resizable_flag = self.windows_resizable  # save the previously stored value
            self.camera_selector.config(state="disabled")
            # Disable labels in Settings menu
            for label in self.labels_actions_menu:
                self.actions_menu.entryconfig(label, state="disabled")
            self.snap_stream_btn.configure(style=self.snap_stream_off_btn_style_name, text=self.snap_stream_off_text)
            if self.snaps_stream_task is None:
                self.pause_snaps_stream = False  # set not to pause repeating assigning the tasks
                self.snaps_stream_task = self.after(15, self.run_snap_stream)
            self.menubar.delete(0, "end")  # delete all entries in menu, effictively hide all menu entries
            self.master.resizable(False, False); self.windows_resizable = False  # make window not resizable forcely
            self.master.wm_overrideredirect(True)  # prevent moving window around, making the UI more stable
            self.focus_force()
        else:
            if self.record_flag:
                self.record_stream()
            # Cancel tasks for running stream and for showing images
            if self.snaps_stream_task is not None:
                self.pause_snaps_stream = True  # prevent assigning new tasks in a stream
                self.after_cancel(self.snaps_stream_task); time.sleep(self.sleep_time_actions_ms); self.snaps_stream_task = None
            if self.show_image_task is not None:
                self.after_cancel(self.show_image_task); time.sleep(self.sleep_time_actions_ms); self.show_image_task = None
            self.snap_image_btn.config(state="normal"); self.record_stream_btn.configure(state="disabled")
            self.fast_fps_overhead = 0  # back to the default value
            # Enable labels in Settings menu
            for label in self.labels_actions_menu:
                self.actions_menu.entryconfig(label, state="normal")
            self.snap_stream_btn.configure(style=self.snap_stream_on_btn_style_name, text=self.snap_stream_on_text)
            self.exp_time_selector.configure(state="normal"); self.camera_selector.config(state="normal")
            self.master.resizable(self.retain_resizable_flag, self.retain_resizable_flag)
            self.windows_resizable = self.retain_resizable_flag  # make window resizable
            self.master.wm_overrideredirect(False)   # restore moving window around
            self.menubar.add_cascade(label="Settings", menu=self.actions_menu)  # restore menubar with adjust size option
            self.focus_force()

    def run_snap_stream(self):
        """
        Perform continuous call for snap_image() method.

        Returns
        -------
        None.

        """
        self.snap_image()  # explicit call for snap function
        if self.snaps_stream_flag and not self.pause_snaps_stream:
            # below - schedule next task, even fast updating should make UI unstable, if show image task queried not so fast
            self.snaps_stream_task = self.after(2, self.run_snap_stream)

    # %% Recording
    def record_stream(self):
        """
        Start / stop recording of single images stream.

        Returns
        -------
        None.

        """
        self.record_flag = not self.record_flag
        if self.record_flag:
            if self.snaps_stream_flag and self.snaps_stream_task is not None:
                self.pause_snaps_stream = True
                self.after_cancel(self.snaps_stream_task)  # make a pause in the live stream
            self.commands2camera.put_nowait("Start Recording"); time.sleep(self.sleep_time_actions_ms/1.5); self.trigger_commands.set()
            time.sleep(self.sleep_time_actions_ms/1.5)
            self.record_stream_btn.configure(style=self.record_stream_off_btn_style_name, text=self.record_stream_off_text)
            if self.snaps_stream_flag:
                self.pause_snaps_stream = False
                self.snaps_stream_task = self.after(4, self.run_snap_stream)  # resume the live stream
        else:
            if self.snaps_stream_flag and self.snaps_stream_task is not None:
                self.pause_snaps_stream = True
                self.after_cancel(self.snaps_stream_task)  # make a pause in the live stream
            self.commands2camera.put_nowait("Stop Recording"); time.sleep(self.sleep_time_actions_ms/1.5); self.trigger_commands.set()
            time.sleep(self.sleep_time_actions_ms/1.5)
            self.record_stream_btn.configure(style=self.record_stream_on_btn_style_name, text=self.record_stream_on_text)
            if self.snaps_stream_flag:
                self.pause_snaps_stream = False
                self.snaps_stream_task = self.after(4, self.run_snap_stream)  # resume the live stream

    # %% Camera settings
    def set_exp_time(self, *args):
        """
        Handle setting of an exposure time.

        Parameters
        ----------
        *args : int
            Provided by tkinter logic.

        Returns
        -------
        None.

        """
        if self.exp_time_selector_wr.validate_input():
            command = ("Set Exposure Time", int(self.exp_time_value.get()))  # explicitly construct a tuple for sending
            self.commands2camera.put_nowait(command)  # send as a command
            time.sleep(self.sleep_time_actions_ms/1.5); self.trigger_commands.set()
            trigger_set = self.trigger_camera_data.wait(timeout=5.5); time.sleep(self.sleep_time_actions_ms/1.5)
            if trigger_set:
                self.trigger_camera_data.clear()  # set to the default state
                self.acquired_images = 0  # reset # of acquired images
                self.fps = 0
                # self.fps_label.config(text=f"Measured FPS: {self.fps}")  # update FPS label
                try:
                    received_data = self.data_from_camera.get_nowait()
                    if isinstance(received_data, int):  # reported assigned exposure time
                        self.exp_time_value.set(received_data)
                    else:
                        print("Report from Camera:", received_data, flush=True)
                except Empty:
                    print("No reported Exposure Time", flush=True)
            else:
                print("Something wrong with Set Exposure Time, the TIMEOUT happened in a trigger wait function", flush=True)
        self.focus()

    def query_fps(self):
        """
        Get the measured FPS from a camera wrapper.

        Returns
        -------
        None.

        """
        self.commands2camera.put_nowait("Get FPS"); time.sleep(self.sleep_time_actions_ms/1.65); self.trigger_commands.set()
        trigger_set = self.trigger_camera_data.wait(timeout=5.0); time.sleep(self.sleep_time_actions_ms/1.65)
        # Dev. Note: pausing by time.sleep() makes the snaps stream mode stable
        if trigger_set:
            self.trigger_camera_data.clear()  # set to the default state
            try:
                received_data = self.data_from_camera.get_nowait()
                if isinstance(received_data, int):
                    self.fps = received_data  # store received FPS
                    self.fps_label.config(text=f"Measured FPS: {self.fps}")  # update FPS label
                else:
                    print("Received from the camera (not integer FPS):", received_data, flush=True)
            except Empty:
                print("No integer FPS received from Queue, but the trigger is set", flush=True)
                self.fps = 0; self.fps_label.config(text=f"Measured FPS: {self.fps}")
        else:
            print("Something wrong with the Query FPS logic, the TIMEOUT happened in a trigger wait function", flush=True)
            self.fps = 0; self.fps_label.config(text=f"Measured FPS: {self.fps}")
        self.update()

    # %% Show acquired image
    def show_image(self):
        """
        Update image by direct request from function (not threaded).

        Returns
        -------
        None.

        """
        # time.sleep(self.image_refresh_delay)
        if self.display_image:
            if self.current_image is not None and isinstance(self.current_image, np.ndarray):
                # Precalculate min / max pixel value on the image
                self.min_pixel_value = np.min(self.current_image); self.max_pixel_value = np.max(self.current_image)
                # Check that the image sizes changed or not, and update the graph accordingly
                img_shape_len = len(self.current_image.shape)  # length of image shape, assuming 2 for grayscaled image, 3 - for RGB (BGR)
                if self.img_w is None and self.img_h is None:
                    if img_shape_len == 2:
                        self.img_h, self.img_w = self.current_image.shape
                    elif img_shape_len == 3:
                        self.img_h, self.img_w, _ = self.current_image.shape
                    else:
                        print("Expect to get grayscaled or RGB image, received other shaped image", flush=True)
                    # Below - automatic change of figure width for adjusting to the ratio of acquired image width / heigt
                    if self.figure_size_w / self.figure_size_h != self.img_w / self.img_h:
                        self.figure_size_h = round(self.figure_size_w*(self.img_h / self.img_w), 1)  # change height of a figure (not shift UI)
                        self.reinitialize_image_figure(True)  # flag for avoiding recall this method in the end of the called method
                else:
                    if img_shape_len == 2:
                        h, w = self.current_image.shape
                    elif img_shape_len == 3:
                        h, w, _ = self.current_image.shape
                    if self.img_h != h or self.img_w != w:
                        # self.refresh_graph()  # refresh container for plotting image with changed width and height
                        self.img_h = h; self.img_w = w
                # Initialize the AxesImage if this function called 1st time
                if self.image_figure_axes is None:
                    self.image_figure_axes = self.image_figure.add_subplot(); self.image_figure_axes.axis('off')
                    self.image_figure.tight_layout()
                    self.image_figure.subplots_adjust(left=0, bottom=0, right=1, top=1)  # remove white borders
                if self.imshowing is None:
                    if img_shape_len == 2:
                        self.imshowing = self.image_figure_axes.imshow(self.current_image, cmap='gray', interpolation='none',
                                                                       vmin=self.min_pixel_value, vmax=self.max_pixel_value)
                    elif img_shape_len == 3:
                        self.imshowing = self.image_figure_axes.imshow(self.current_image, interpolation='none')
                    else:
                        self.imshowing = self.image_figure_axes.imshow(self.current_image)
                    # self.imshowing.format_cursor_data = self.cursor_wrapper  # remove pixel value in [...] on a widget
                    self.imshowing.set_data(self.current_image)  # set data for AxesImage for updating image content
                    self.image_canvas.draw_idle()
                else:
                    self.imshowing.set_data(self.current_image)  # set data for AxesImage for updating image content
                    self.imshowing.set_clim(vmin=self.min_pixel_value, vmax=self.max_pixel_value)
                    self.image_canvas.draw_idle()
                # assuming that image intensities are integer values (float image is [0, 1] range of pixel values)
                if isinstance(self.max_pixel_value, float) and self.max_pixel_value > 1.1:
                    self.max_pixel_value = int(np.round(self.max_pixel_value, 0))
                    self.min_pixel_value = int(np.round(self.max_pixel_value, 0))
            self.display_image = False

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
            self.snap_stream_btn.configure(state="disabled"); self.snap_image_btn.configure(state="disabled")
            self.exp_time_selector.configure(state="disabled")
            print("Selected camera:", selected_camera)
            self.img_w = None; self.img_h = None  # put image WxH to the default values
            if not self.check_installed_drivers(selected_camera):
                print(f"The required drivers for the '{selected_camera}' camera not installed. \nThe previously active camera remained")
                self.selected_camera.set(self.active_camera)  # set back the active camera and open it
            else:
                self.close_camera()  # closing the currently active camera
                self.clean_queues_events()  # cleaning the queues for reconnecting to the new instance of a Camera class
                self.open_camera()
                if not self.camera_opened:
                    print("Camera not opened, going back to the Simulated", flush=True)
                    self.close_camera(); self.clean_queues_events()
                    self.selected_camera.set(self.supported_cameras[0]); self.open_camera()
                else:
                    self.active_camera = self.selected_camera.get()
            self.snap_stream_btn.configure(state="normal"); self.snap_image_btn.configure(state="normal")
            self.exp_time_selector.configure(state="normal")

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
        elif selected_camera == self.supported_cameras[1]:  # should be embedded in a laptop
            try:
                import cv2  # minimal requirement - installed pyopencv library
                if cv2 is not None:
                    return True
                else:
                    return False
            except ModuleNotFoundError:
                return False
        elif selected_camera == self.supported_cameras[2]:  # next camera
            return False  # implement checking logic for a next camera

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

    def reinitialize_image_figure(self, avoid_show_image: bool = False):
        """
        Reinitialize the figure with update sizes.

        Returns
        -------
        None.

        """
        self.plot_widget.destroy(); self.buttons_frame.pack_forget()
        del self.imshowing; del self.image_figure_axes; del self.image_figure
        self.image_figure = pltFigure.Figure(figsize=(self.figure_size_w, self.figure_size_h))  # empty figure with changed
        self.image_canvas = FigureCanvasTkAgg(self.image_figure, master=self); self.plot_widget = self.image_canvas.get_tk_widget()
        self.plot_widget.pack(side=LEFT, padx=self.padx, pady=self.pady); self.buttons_frame.pack(side=TOP, padx=self.padx, pady=self.pady)
        self.image_figure.set_figwidth(self.figure_size_w); self.image_figure.set_figheight(self.figure_size_h)
        self.image_figure_axes = None; self.imshowing = None
        if self.current_image is not None and not avoid_show_image:  # if there was some current image displayed, it will redisplay it
            self.display_image = True  # explicit flag for displaying an image
            self.after(2, self.show_image)  # schedule asynchronous call to show an image

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
        if self.snaps_stream_flag:
            self.snap_stream()  # simulates click on stop stream button
        if self.camera_opened:
            self.camera_status_label.config(text=self.camera_act_text, style=self.camera_init_status_style); self.update()
            self.commands2camera.put_nowait("Stop"); time.sleep(self.sleep_time_actions_ms); self.trigger_commands.set()
            trigger_set = self.trigger_camera_data.wait(4.0); time.sleep(self.sleep_time_actions_ms)
            if trigger_set:
                try:
                    received_data = self.data_from_camera.get_nowait()
                    if isinstance(received_data, str):
                        print(f"{self.active_camera} Camera", received_data, "and Closed")
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
            self.camera_opened = False  # default flag for opened / closed separate controlling Process for a camera

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
